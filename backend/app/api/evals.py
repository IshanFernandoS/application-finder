from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import BaselineRunRequest
from ..services.evaluation_service import EvaluationService
from .utils import raise_http

router = APIRouter(prefix="/evals", tags=["evaluation"])


@router.post("/run")
def run(scope_id: str = "electromagnetic_functional_materials", mode: str = "full_method", db: Session = Depends(get_db)):
    try:
        return EvaluationService().run(db, scope_id, mode=mode)
    except Exception as exc:
        raise_http(exc)


@router.get("/results")
def results(db: Session = Depends(get_db)):
    return EvaluationService().list_results(db)


@router.post("/baselines/run")
def baselines_run(request: BaselineRunRequest, db: Session = Depends(get_db)):
    try:
        return EvaluationService().run_baseline(db, request)
    except Exception as exc:
        raise_http(exc)


@router.get("/baselines/results")
def baselines_results(db: Session = Depends(get_db)):
    return EvaluationService().baseline_results(db)
