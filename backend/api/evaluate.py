import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request

from backend.database import save_evaluation, verify_session_token
from backend.models.evaluation import (
    EvaluationRequest,
    EvaluationResponse,
)
from evaluation.orchestrator import evaluate_request


router = APIRouter(
    prefix="/evaluate",
    tags=["Evaluation"],
)
logger = logging.getLogger(__name__)


def _read_token(request: Request) -> Optional[str]:
    authorization = request.headers.get("authorization")
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return request.cookies.get("aegiseval_token")


@router.post(
    "",
    response_model=EvaluationResponse,
)
def evaluate(
    payload: EvaluationRequest,
    request: Request,
) -> EvaluationResponse:
    """Evaluate an AI response using the configured local evaluation engine."""

    try:
        result = evaluate_request(payload)
        token = _read_token(request)
        session = verify_session_token(token) if token else None
        if session:
            evaluation_payload = {
                "question": result.question,
                "response": result.response,
                "reference_answer": payload.reference_answer,
                "verdict": result.verdict,
                "overall_score": result.overall_score,
                "metrics": {
                    "relevance": result.relevance.model_dump(),
                    "factuality": result.factuality.model_dump(),
                    "faithfulness": result.faithfulness.model_dump(),
                    "completeness": result.completeness.model_dump(),
                    "hallucination": result.hallucination.model_dump(),
                    "semantic_similarity": result.semantic_similarity.model_dump(),
                },
            }
            save_evaluation(session["id"], evaluation_payload)
        return result

    except ValueError as error:
        raise HTTPException(
            status_code=422,
            detail=str(error),
        ) from error

    except Exception as error:
        logger.exception("Evaluation request failed")
        raise HTTPException(
            status_code=500,
            detail="Evaluation could not be completed. Please retry, and check the backend logs if it continues.",
        ) from error


@router.get("/history")
def evaluation_history(request: Request) -> dict[str, list[dict[str, Any]]]:
    from backend.api.auth import get_authenticated_user
    from backend.database import get_user_evaluations

    user = get_authenticated_user(request)
    return {"evaluations": get_user_evaluations(user["id"]) }
