from fastapi import APIRouter


router = APIRouter(tags=["System"])


@router.get("/health")
def health_check() -> dict[str, str]:
    """Report whether the backend process is available."""
    return {
        "status": "healthy",
        "service": "LLM Evaluation API",
    }