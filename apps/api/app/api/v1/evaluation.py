from pathlib import Path

from fastapi import APIRouter

from app.schemas.evaluation import EvaluationSummaryResponse
from app.services.evaluation import DEFAULT_BENCHMARK_PATH, evaluate_dataset_file

router = APIRouter(prefix="/evaluation", tags=["Evaluation"])


@router.get("/summary", response_model=EvaluationSummaryResponse)
def get_evaluation_summary():
    dataset = evaluate_dataset_file(DEFAULT_BENCHMARK_PATH)
    return EvaluationSummaryResponse(**dataset)
