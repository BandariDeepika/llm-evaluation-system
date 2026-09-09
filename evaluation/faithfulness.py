from typing import Optional
from evaluation.common import EvaluationResult, split_claims, supported_claims


def evaluate_faithfulness(ai_response: str, context: Optional[str]) -> EvaluationResult:
    """Estimate groundedness by checking response claims against available context."""
    if not context or not context.strip():
        return EvaluationResult(score=None, explanation="Faithfulness is uncertain because no supplied or retrieved context is available.", details={"unsupported_claims": [], "certainty": "uncertain"})
    claims = split_claims(ai_response)
    supported, unsupported = supported_claims(claims, context)
    return EvaluationResult(
        score=round(10 * len(supported) / max(len(claims), 1), 2),
        explanation="Rule-based groundedness estimate based on claim overlap with the supplied context; it is not an LLM judgment.",
        details={"unsupported_claims": unsupported, "supported_claims": supported},
    )