from functools import lru_cache
from typing import Optional
from evaluation.common import EvaluationResult, clamp_score

@lru_cache(maxsize=1)
def _get_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


def evaluate_semantic_similarity(ai_response: str, reference_answer: Optional[str]) -> EvaluationResult:
    """Calculate cosine similarity using the all-MiniLM-L6-v2 embedding model."""
    if not ai_response.strip():
        raise ValueError("ai_response must contain text")
    if not reference_answer or not reference_answer.strip():
        return EvaluationResult(score=None, explanation="Semantic similarity is unavailable because no reference answer was supplied.", details={"similarity": None, "certainty": "unavailable"})
    model = _get_model()
    embeddings = model.encode([ai_response, reference_answer], normalize_embeddings=True)
    similarity = float(embeddings[0] @ embeddings[1])
    normalized_score = clamp_score(((similarity + 1) / 2) * 10)
    return EvaluationResult(
        score=normalized_score,
        explanation="Cosine similarity between normalized all-MiniLM-L6-v2 embeddings.",
        details={"similarity": round(similarity, 4), "model": "all-MiniLM-L6-v2"},
    )