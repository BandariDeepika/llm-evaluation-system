from typing import Optional

from evaluation.common import EvaluationResult, clamp_score, tokenize


def _split_aspects(text: str) -> list[str]:
    """Split text into simple sentence-level expected aspects."""
    aspects = [
        part.strip()
        for part in text.replace("?", ".").replace("!", ".").split(".")
        if part.strip()
    ]

    return aspects


def _aspect_words(text: str) -> set[str]:
    """Return normalized words used for aspect comparison."""
    return tokenize(text)


def evaluate_completeness(
    question: str,
    ai_response: str,
    reference_answer: Optional[str] = None,
    context: Optional[str] = None,
) -> EvaluationResult:
    """
    Evaluate whether the AI response addresses the expected information.

    When a reference answer is available, expected aspects are derived
    from the reference answer.

    When no reference answer is available, supplied context is used
    when available.
    """

    if not question.strip() or not ai_response.strip():
        raise ValueError(
            "question and ai_response must contain text"
        )

    target_text = None
    target_name = "question"

    if reference_answer and reference_answer.strip():
        target_text = reference_answer.strip()
        target_name = "reference_answer"

    elif context and context.strip():
        target_text = context.strip()
        target_name = "retrieved_context"

    # ---------------------------------------------------------
    # Reference/context based completeness evaluation
    # ---------------------------------------------------------
    if target_text:
        aspects = _split_aspects(target_text)

        response_words = _aspect_words(ai_response)

        addressed_aspects = []
        partial_aspects = []
        missing_aspects = []

        for aspect in aspects:
            aspect_words = _aspect_words(aspect)

            if not aspect_words:
                continue

            overlap = aspect_words.intersection(response_words)
            coverage = len(overlap) / len(aspect_words)

            if coverage >= 0.75:
                addressed_aspects.append(aspect)

            elif coverage >= 0.30:
                partial_aspects.append(aspect)

            else:
                missing_aspects.append(aspect)

        total_aspects = (
            len(addressed_aspects)
            + len(partial_aspects)
            + len(missing_aspects)
        )

        if total_aspects == 0:
            score = 0.0

        else:
            score = (
                10
                * (
                    len(addressed_aspects)
                    + 0.5 * len(partial_aspects)
                )
                / total_aspects
            )

        if missing_aspects and partial_aspects:
            reasoning = (
                "The response addresses some expected information "
                "but partially covers or omits other aspects."
            )

        elif missing_aspects:
            reasoning = (
                "The response does not address all expected "
                "information from the evaluation target."
            )

        elif partial_aspects:
            reasoning = (
                "The response addresses the expected information "
                "but some aspects are only partially covered."
            )

        else:
            reasoning = (
                "The response addresses the expected information "
                "contained in the evaluation target."
            )

    # ---------------------------------------------------------
    # No reference/context available
    # ---------------------------------------------------------
    else:
        response_words = _aspect_words(ai_response)

        if response_words:
            score = 8.0
            addressed_aspects = [
                "The response provides an answer to the submitted question."
            ]
            partial_aspects = []
            missing_aspects = []

            reasoning = (
                "No reference answer or retrieved context was "
                "available. A positive baseline is assigned because "
                "the response contains evaluable information."
            )

        else:
            score = 0.0
            addressed_aspects = []
            partial_aspects = []
            missing_aspects = [
                "No answer content was provided."
            ]

            reasoning = (
                "The response does not contain enough information "
                "to evaluate completeness."
            )

    return EvaluationResult(
        score=clamp_score(score),
        explanation=reasoning,
        details={
            "addressed_aspects": addressed_aspects,
            "partial_aspects": partial_aspects,
            "missing_aspects": missing_aspects,

            # Keep the old field for compatibility with M2/frontend.
            "missing_information": missing_aspects,

            "target": target_name,
            "reasoning": reasoning,
        },
    )