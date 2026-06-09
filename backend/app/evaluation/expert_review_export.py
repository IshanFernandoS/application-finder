from __future__ import annotations

import csv
from pathlib import Path
from typing import List

from ..schemas import FBSPMPathway


def export_expert_review(path: Path, pathways: List[FBSPMPathway]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["pathway_id", "title", "function", "mechanism", "device_route", "uncertainty", "review_notes"])
        for pathway in pathways:
            writer.writerow(
                [
                    pathway.pathway_id,
                    pathway.title,
                    pathway.function,
                    pathway.behaviour_or_mechanism,
                    pathway.structure_or_device_realization,
                    pathway.uncertainty,
                    "",
                ]
            )
    return str(path)
