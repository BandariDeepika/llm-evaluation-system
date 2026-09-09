from typing import Optional
from evaluation.common import EvaluationResult, split_claims, supported_claims


def evaluate_factuality(
    question: str,
    ai_response: str,
    reference_answer: Optional[str] = None,
    context: Optional[str] = None,
) -> EvaluationResult:
    """Estimate factual support against supplied evidence, without inventing facts."""
    del question
    evidence = " ".join(value for value in (reference_answer, context) if value and value.strip())
    if not evidence:
        return EvaluationResult(score=None, explanation="Factuality is unavailable because no reference information or context was supplied.", details={"unsupported_claims": [], "certainty": "uncertain"})
    claims = split_claims(ai_response)
    supported, unsupported = supported_claims(claims, evidence)
    score = 10 * len(supported) / max(len(claims), 1)
    return EvaluationResult(
        score=round(score, 2),
        explanation="Rule-based factuality estimate based on claim overlap with supplied evidence; it does not prove truth and should later be replaced or supplemented by an LLM judge.",
        details={"unsupported_claims": unsupported, "supported_claims": supported},
    )