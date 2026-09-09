from fastapi import APIRouter, HTTPException

from backend.models.evaluation import EvaluationRequest, EvaluationResponse
from evaluation.orchestrator import evaluate_request


router = APIRouter(prefix="/evaluate", tags=["Evaluation"])


@router.post("", response_model=EvaluationResponse)
def evaluate(payload: EvaluationRequest) -> EvaluationResponse:
    """Evaluate an AI response using the configured local evaluation engine."""
    try:
        return evaluate_request(payload)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail="Evaluation could not be completed.") from error