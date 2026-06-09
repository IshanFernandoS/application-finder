from __future__ import annotations

import json
from typing import List

from sqlalchemy.orm import Session

from ..config import settings
from ..database import ApplicationNodeRecord, EvidenceRecord
from ..exceptions import ConfigurationError, DependencyUnavailableError, ValidationFailure
from ..prompts import DESCRIPTOR_EXTRACTION_SYSTEM_PROMPT
from ..schemas import ApplicationNode, Scope
from .ids import stable_id
from .serialization import model_to_dict


class DescriptorExtractionService:
    def extract_for_scope(self, db: Session, scope: Scope, limit: int = 50) -> List[ApplicationNode]:
        if not settings.openai_api_key or not settings.enable_openai_reasoning:
            raise ConfigurationError("Descriptor extraction requires ENABLE_OPENAI_REASONING=true and OPENAI_API_KEY.")
        try:
            from openai import OpenAI  # type: ignore
        except Exception as exc:
            raise DependencyUnavailableError("Install the OpenAI Python SDK to run descriptor extraction.") from exc

        client = OpenAI(api_key=settings.openai_api_key)
        chunks = db.query(EvidenceRecord).limit(limit).all()
        nodes: List[ApplicationNode] = []
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
                "required_fields": list(ApplicationNode.__fields__.keys()),
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
                raw_nodes = payload.get("application_nodes", payload if isinstance(payload, list) else [])
                if isinstance(raw_nodes, dict):
                    raw_nodes = [raw_nodes]
                for raw in raw_nodes:
                    raw.setdefault("node_id", stable_id("node", evidence["evidence_id"], raw.get("label", "")))
                    raw.setdefault("source_ids", [evidence["document_id"]])
                    raw.setdefault("evidence_ids", [evidence["evidence_id"]])
                    raw.setdefault("evidence_count", 1)
                    node = ApplicationNode(**raw)
                    record_existing = db.get(ApplicationNodeRecord, node.node_id)
                    if record_existing:
                        record_existing.payload = model_to_dict(node)
                    else:
                        db.add(
                            ApplicationNodeRecord(
                                node_id=node.node_id,
                                scope_id=scope.scope_id,
                                cluster_id=node.cluster_id,
                                payload=model_to_dict(node),
                            )
                        )
                    nodes.append(node)
            except Exception as exc:
                raise ValidationFailure(f"OpenAI descriptor output failed ApplicationNode validation: {exc}") from exc
        db.commit()
        return nodes
