import json

from fastapi import APIRouter, HTTPException

from app.schemas.evaluation import EvaluationSummaryResponse
from app.services.evaluation import DEFAULT_RESULTS_PATH

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


@router.get("/summary", response_model=EvaluationSummaryResponse)
def get_evaluation_summary():
    try:
        with DEFAULT_RESULTS_PATH.open("r", encoding="utf-8") as handle:
            result = json.load(handle)
        metrics = result.get("metrics") if isinstance(result, dict) else None
        if not isinstance(metrics, dict):
            raise ValueError("metrics missing")
        return EvaluationSummaryResponse(**metrics)
    except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError, ValueError, OSError) as exc:
        raise HTTPException(status_code=404, detail="No evaluation result is available.") from exc
