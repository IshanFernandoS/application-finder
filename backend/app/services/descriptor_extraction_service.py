from __future__ import annotations

import json
from typing import Any, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import settings
from ..database import ApplicationNodeRecord, EvidenceRecord
from ..exceptions import ConfigurationError, DependencyUnavailableError, ValidationFailure
from ..prompts import DESCRIPTOR_EXTRACTION_SYSTEM_PROMPT
from ..schemas import ApplicationNode, Scope
from .ids import stable_id
from .serialization import model_to_dict


class DescriptorExtractionService:
    em_keywords = (
        "electromagnetic",
        "metamaterial",
        "metasurface",
        "microwave",
        "rf",
        "terahertz",
        "thz",
        "photonic",
        "optical",
        "infrared",
        "dielectric",
        "permittivity",
        "permeability",
        "antenna",
        "absorber",
        "shielding",
        "plasmonic",
        "emissivity",
        "frequency-selective",
        "radome",
    )

    def extract_for_scope(
        self, db: Session, scope: Scope, limit: int = 50, evidence_ids: List[str] | None = None
    ) -> List[ApplicationNode]:
        if not settings.openai_api_key or not settings.enable_openai_reasoning:
            raise ConfigurationError("Descriptor extraction requires ENABLE_OPENAI_REASONING=true and OPENAI_API_KEY.")
        try:
            from openai import OpenAI  # type: ignore
        except Exception as exc:
            raise DependencyUnavailableError("Install the OpenAI Python SDK to run descriptor extraction.") from exc

        client = OpenAI(api_key=settings.openai_api_key)
        query = db.query(EvidenceRecord)
        if evidence_ids:
            query = query.filter(EvidenceRecord.evidence_id.in_(evidence_ids))
        chunks = query.order_by(func.length(EvidenceRecord.text).desc()).limit(limit).all()
        nodes: List[ApplicationNode] = []
        field_source = getattr(ApplicationNode, "model_fields", None) or ApplicationNode.__fields__
        field_names = list(field_source.keys())
        for record in chunks:
            evidence = record.payload
            prompt = {
                "scope": model_to_dict(scope),
                "evidence": {
                    "evidence_id": evidence["evidence_id"],
                    "title": evidence["title"],
                    "year": evidence.get("year"),
                    "doi": evidence.get("doi"),
                    "text": evidence["text"][:6000],
                },
                "output_contract": {"application_nodes": [{field: "<value>" for field in field_names}]},
                "required_fields": field_names,
                "instructions": [
                    "Return JSON only.",
                    "Use the key application_nodes.",
                    "Extract 1-3 descriptors for in-scope electromagnetic evidence.",
                    "Use low confidence for title-only or metadata-only evidence.",
                    "Do not recommend generated materials in this extraction step.",
                ],
            }
            response = client.chat.completions.create(
                model=settings.openai_model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": DESCRIPTOR_EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": json.dumps(prompt)},
                ],
            )
            content = response.choices[0].message.content or "{}"
            try:
                payload = json.loads(content)
                raw_nodes = self._extract_raw_nodes(payload)
                extracted = self._nodes_from_raw(db, scope, evidence, raw_nodes)
                if not extracted:
                    fallback = self._fallback_node(scope, evidence)
                    extracted = [fallback] if fallback else []
                    for node in extracted:
                        self._upsert_node(db, scope, node)
                nodes.extend(extracted)
            except Exception as exc:
                raise ValidationFailure(f"OpenAI descriptor output failed ApplicationNode validation: {exc}") from exc
        db.commit()
        return nodes

    def _extract_raw_nodes(self, payload: Any) -> List[dict]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if not isinstance(payload, dict):
            return []
        for key in ("application_nodes", "nodes", "descriptors"):
            value = payload.get(key)
            if isinstance(value, dict):
                return [value]
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        if any(field in payload for field in ("label", "application_text", "domain", "function")):
            return [payload]
        return []

    def _nodes_from_raw(self, db: Session, scope: Scope, evidence: dict, raw_nodes: List[dict]) -> List[ApplicationNode]:
        nodes: List[ApplicationNode] = []
        errors: List[str] = []
        for raw in raw_nodes:
            try:
                normalized = self._normalize_raw_node(scope, evidence, raw)
                node = ApplicationNode(**normalized)
                self._upsert_node(db, scope, node)
                nodes.append(node)
            except Exception as exc:
                errors.append(str(exc))
        if raw_nodes and not nodes:
            fallback = self._fallback_node(scope, evidence)
            if fallback:
                self._upsert_node(db, scope, fallback)
                nodes.append(fallback)
            elif errors:
                raise ValidationFailure("; ".join(errors))
        return nodes

    def _normalize_raw_node(self, scope: Scope, evidence: dict, raw: dict) -> dict:
        node = dict(raw)
        defaults = self._fallback_node_values(scope, evidence)
        for key, value in defaults.items():
            if node.get(key) in (None, "", []):
                node[key] = value
        node["node_id"] = node.get("node_id") or stable_id("node", evidence["evidence_id"], node.get("label", ""))
        node["source_ids"] = node.get("source_ids") or [evidence["document_id"]]
        node["evidence_ids"] = node.get("evidence_ids") or [evidence["evidence_id"]]
        node["evidence_count"] = node.get("evidence_count") or 1
        node["confidence"] = max(0.0, min(float(node.get("confidence", defaults["confidence"]) or 0.0), 1.0))
        return node

    def _fallback_node(self, scope: Scope, evidence: dict) -> ApplicationNode | None:
        combined = f"{evidence.get('title', '')}\n{evidence.get('text', '')}".lower()
        if not any(keyword in combined for keyword in self.em_keywords):
            return None
        return ApplicationNode(**self._fallback_node_values(scope, evidence))

    def _fallback_node_values(self, scope: Scope, evidence: dict) -> dict:
        title = str(evidence.get("title") or "Electromagnetic application descriptor").strip()
        text = str(evidence.get("text") or title).strip()
        combined = f"{title}\n{text}".lower()
        label = title[:90]
        metadata_only = evidence.get("section") == "metadata" or "no abstract was available" in combined
        return {
            "node_id": stable_id("node", evidence["evidence_id"], label),
            "label": label,
            "application_text": text[:900],
            "domain": self._guess_domain(scope, combined),
            "function": self._guess_function(combined),
            "device_type": self._guess_device_type(combined),
            "physical_em_mechanism": self._guess_mechanism(combined),
            "material_class": self._guess_material_class(combined),
            "em_property_requirements": self._guess_property_requirements(combined),
            "source_ids": [evidence["document_id"]],
            "evidence_ids": [evidence["evidence_id"]],
            "year": evidence.get("year"),
            "confidence": 0.28 if metadata_only else 0.45,
            "evidence_count": 1,
        }

    def _guess_domain(self, scope: Scope, combined: str) -> str:
        priority_matches = (
            (("metamaterial", "metasurface"), "metamaterials and metasurfaces"),
            (("absorber", "absorption"), "absorbers"),
            (("antenna",), "antennas and antenna substrates"),
            (("shield", "emi"), "electromagnetic interference shielding"),
            (("frequency-selective", "frequency selective"), "frequency-selective surfaces"),
            (("radome",), "radomes"),
            (("thermal", "emissivity"), "infrared and thermal-emissivity devices"),
            (("photonic", "optical"), "photonic coatings"),
            (("phase-change", "phase change"), "phase-change electromagnetic materials"),
            (("plasmonic",), "plasmonic materials"),
        )
        available_domains = set(scope.included_domains)
        for keywords, domain in priority_matches:
            if domain in available_domains and any(keyword in combined for keyword in keywords):
                return domain
        generic_tokens = {"electromagnetic", "material", "materials", "device", "devices", "functional"}
        for domain in scope.included_domains:
            tokens = domain.lower().replace("/", " ").replace("-", " ").split()
            if any(
                len(token) > 4 and token not in generic_tokens and token.rstrip("s") in combined
                for token in tokens
            ):
                return domain
        return scope.included_domains[0] if scope.included_domains else "electromagnetic functional materials"

    def _guess_function(self, combined: str) -> str:
        if "inverse design" in combined:
            return "inverse design of electromagnetic response"
        if "absorber" in combined or "absorption" in combined:
            return "electromagnetic absorption control"
        if "shield" in combined:
            return "electromagnetic interference shielding"
        if "antenna" in combined:
            return "antenna performance enhancement"
        if "effective medium" in combined:
            return "effective-medium electromagnetic response modeling"
        return "electromagnetic response engineering"

    def _guess_device_type(self, combined: str) -> str | None:
        for keyword, device_type in (
            ("metasurface", "metasurface"),
            ("metamaterial", "metamaterial"),
            ("absorber", "absorber"),
            ("antenna", "antenna substrate"),
            ("shield", "shielding layer"),
            ("radome", "radome"),
            ("frequency-selective", "frequency-selective surface"),
        ):
            if keyword in combined:
                return device_type
        return None

    def _guess_mechanism(self, combined: str) -> str | None:
        for keyword, mechanism in (
            ("effective medium", "effective-medium electromagnetic response"),
            ("permittivity", "dielectric polarization"),
            ("permeability", "magnetic response"),
            ("plasmon", "plasmonic resonance"),
            ("impedance", "impedance matching"),
            ("emissivity", "thermal electromagnetic emission control"),
        ):
            if keyword in combined:
                return mechanism
        return None

    def _guess_material_class(self, combined: str) -> str | None:
        for keyword, material_class in (
            ("metamaterial", "metamaterials"),
            ("dielectric", "dielectrics"),
            ("ceramic", "ceramics"),
            ("oxide", "oxides"),
            ("chalcogenide", "chalcogenides"),
            ("plasmonic", "plasmonic materials"),
        ):
            if keyword in combined:
                return material_class
        return None

    def _guess_property_requirements(self, combined: str) -> List[str]:
        requirements = []
        for keyword, requirement in (
            ("permittivity", "complex permittivity"),
            ("permeability", "complex permeability"),
            ("loss", "loss tangent"),
            ("conductivity", "conductivity"),
            ("refractive", "refractive index"),
            ("emissivity", "emissivity"),
            ("band gap", "band gap"),
        ):
            if keyword in combined:
                requirements.append(requirement)
        return requirements

    def _upsert_node(self, db: Session, scope: Scope, node: ApplicationNode) -> None:
        record_existing = db.get(ApplicationNodeRecord, node.node_id)
        if record_existing:
            record_existing.payload = model_to_dict(node)
            record_existing.scope_id = scope.scope_id
            record_existing.cluster_id = node.cluster_id
            return
        db.add(
            ApplicationNodeRecord(
                node_id=node.node_id,
                scope_id=scope.scope_id,
                cluster_id=node.cluster_id,
                payload=model_to_dict(node),
            )
        )
