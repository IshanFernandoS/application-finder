from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from ..exceptions import ConfigurationError
from ..schemas import MaterialCandidate, MatterGenConstraintSet
from .mattergen_setup_service import MatterGenSetupService


class MatterGenAdapter:
    def run(self, constraint_set: MatterGenConstraintSet, output_dir: Path) -> List[MaterialCandidate]:
        status = MatterGenSetupService().status()
        if status.status != "available":
            raise ConfigurationError(f"MatterGen is not available: {status.status}")
        # The real local/remote execution point is intentionally narrow. A GPU
        # worker implementation should write structures to output_dir and return
        # parsed generated candidates after validation hooks run.
        raise ConfigurationError("MatterGen worker execution is not configured in this local environment.")

    def remote_payload(self, constraint_set: MatterGenConstraintSet) -> Dict[str, object]:
        return {
            "compatible_constraints": constraint_set.compatible_constraints,
            "unsupported_em_properties": [req.dict() for req in constraint_set.unsupported_em_properties],
        }
