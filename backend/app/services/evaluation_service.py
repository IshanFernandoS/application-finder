from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Dict, List

from sqlalchemy.orm import Session

from ..config import settings
from ..database import (
    ApplicationClusterRecord,
    ApplicationNodeRecord,
    EvaluationRunRecord,
    GapRecord,
    PathwayRecord,
)
from ..evaluation.application_space_eval import application_space_metrics
from ..evaluation.baseline_runner import BaselineRunner
from ..evaluation.descriptor_eval import descriptor_metrics
from ..evaluation.fbs_pm_eval import fbs_pm_metrics
from ..evaluation.gap_eval import gap_metrics
from ..evaluation.time_split_eval import time_split_support
from ..schemas import (
    ApplicationCluster,
    ApplicationNode,
    BaselineRunRequest,
    EvaluationRun,
    FBSPMPathway,
    Gap,
    MetricResult,
)
from .ids import new_id
from .object_storage_service import ObjectStorageService
from .serialization import model_to_dict


class EvaluationService:
    def run(self, db: Session, scope_id: str, mode: str = "full_method") -> EvaluationRun:
        nodes = [ApplicationNode(**record.payload) for record in db.query(ApplicationNodeRecord).filter(ApplicationNodeRecord.scope_id == scope_id)]
        clusters = [
            ApplicationCluster(**record.payload)
            for record in db.query(ApplicationClusterRecord).filter(ApplicationClusterRecord.scope_id == scope_id)
        ]
        gaps = [Gap(**record.payload) for record in db.query(GapRecord).filter(GapRecord.scope_id == scope_id)]
        gap_ids = {gap.gap_id for gap in gaps}
        pathways = [
            FBSPMPathway(**record.payload)
            for record in db.query(PathwayRecord).all()
            if record.gap_id in gap_ids
        ]
        metrics_dict: Dict[str, float] = {}
        metrics_dict.update(descriptor_metrics(nodes))
        metrics_dict.update(application_space_metrics(nodes, clusters))
        metrics_dict.update(gap_metrics(gaps))
        metrics_dict.update(fbs_pm_metrics(pathways))
        later_nodes = [node for node in nodes if node.year and node.year >= 2020]
        metrics_dict.update(time_split_support(pathways, later_nodes))
        metrics = [MetricResult(name=name, value=value) for name, value in sorted(metrics_dict.items())]
        run = EvaluationRun(
            run_id=new_id("eval"),
            scope_id=scope_id,
            mode=mode,
            created_at=datetime.now(timezone.utc).isoformat(),
            metrics=metrics,
            warnings=[] if nodes else ["No descriptor nodes exist yet; run ingestion and extraction for meaningful metrics."],
        )
        artifact_path = settings.output_dir / f"eval_{run.run_id}.json"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(json.dumps(model_to_dict(run), indent=2), encoding="utf-8")
        run.artifacts["json"] = ObjectStorageService().upload_file(
            artifact_path,
            f"evaluations/{run.run_id}/{artifact_path.name}",
            content_type="application/json",
        )
        db.add(EvaluationRunRecord(run_id=run.run_id, scope_id=scope_id, mode=mode, payload=model_to_dict(run)))
        db.commit()
        return run

    def list_results(self, db: Session) -> List[EvaluationRun]:
        return [EvaluationRun(**record.payload) for record in db.query(EvaluationRunRecord).order_by(EvaluationRunRecord.created_at.desc())]

    def run_baseline(self, db: Session, request: BaselineRunRequest) -> Dict[str, object]:
        return BaselineRunner().run(db, request)

    def baseline_results(self, db: Session) -> List[EvaluationRun]:
        return [run for run in self.list_results(db) if run.mode.startswith("baseline")]
