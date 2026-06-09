from __future__ import annotations

import json
from typing import List

from ..config import settings
from ..exceptions import ConfigurationError, DependencyUnavailableError, ValidationFailure
from ..prompts import FBS_PM_SYSTEM_PROMPT
from ..schemas import EvidenceChunk, FBSPMPathway, Gap, Scope


class FBSPMGenerator:
    def generate(self, scope: Scope, gap: Gap, evidence: List[EvidenceChunk]) -> List[FBSPMPathway]:
        if not settings.openai_api_key or not settings.enable_openai_reasoning:
            raise ConfigurationError("FBS-PM generation requires ENABLE_OPENAI_REASONING=true and OPENAI_API_KEY.")
        try:
            from openai import OpenAI  # type: ignore
        except Exception as exc:
            raise DependencyUnavailableError("Install the OpenAI Python SDK to run FBS-PM generation.") from exc
        client = OpenAI(api_key=settings.openai_api_key)
        prompt = {
            "scope": scope.dict(),
            "gap": gap.dict(),
            "boundary_evidence": [chunk.dict() for chunk in evidence[:16]],
            "required_chain": [
                "Gap",
                "Pseudo-application",
                "Function",
                "Behaviour / physical EM mechanism",
                "Structure / device realization pathway",
                "EM material-property envelope",
                "material candidate",
                "evidence / uncertainty / validation status",
            ],
        }
        response = client.chat.completions.create(
            model=settings.openai_model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": FBS_PM_SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(prompt)},
            ],
        )
        raw = json.loads(response.choices[0].message.content or "{}")
        raw_pathways = raw.get("pathways", raw if isinstance(raw, list) else [])
        if isinstance(raw_pathways, dict):
            raw_pathways = [raw_pathways]
        try:
            return [FBSPMPathway(**item) for item in raw_pathways]
        except Exception as exc:
            raise ValidationFailure(f"OpenAI FBS-PM output failed schema validation: {exc}") from exc
