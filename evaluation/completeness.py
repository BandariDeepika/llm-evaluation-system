from typing import Optional

from evaluation.common import EvaluationResult, clamp_score, tokenize


def evaluate_completeness(
    question: str,
    ai_response: str,
    reference_answer: Optional[str] = None,
) -> EvaluationResult:
    """Estimate completeness using reference-answer terms or answer coverage."""

    if not question.strip() or not ai_response.strip():
        raise ValueError("question and ai_response must contain text")

    # If a reference answer is available, compare against it.
    if reference_answer and reference_answer.strip():
        target_words = tokenize(reference_answer)
        response_words = tokenize(ai_response)

        missing = sorted(target_words - response_words)

        score = 10 * (
            1 - len(missing) / max(len(target_words), 1)
        )

        target_name = "reference_answer"

    else:
        # For short direct answers, avoid comparing answer words
        # directly with question words.
        response_words = tokenize(ai_response)

        if response_words:
            score = 8.0
        else:
            score = 0.0

        missing = []
        target_name = "question"

    return EvaluationResult(
        score=clamp_score(score),
        explanation=(
            "Rule-based completeness estimate. "
            "Short direct answers receive a positive baseline when "
            "no reference answer is provided."
        ),
        details={
            "missing_information": missing,
            "target": target_name,
        },
    )