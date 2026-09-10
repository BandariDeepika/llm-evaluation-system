from typing import Optional

from evaluation.common import (
    EvaluationResult,
    split_claims,
    supported_claims,
)


def evaluate_faithfulness(
    ai_response: str,
    context: Optional[str],
) -> EvaluationResult:

    if not ai_response.strip():
        raise ValueError("ai_response must contain text")

    if not context or not context.strip():
        return EvaluationResult(
            score=None,
            explanation=(
                "Faithfulness is uncertain because no supplied "
                "or retrieved context is available."
            ),
            details={
                "unsupported_claims": [],
                "supported_claims": [],
                "certainty": "uncertain",
            },
        )

    claims = split_claims(ai_response)

    if not claims:
        return EvaluationResult(
            score=0.0,
            explanation=(
                "No evaluable claims were found in the response."
            ),
            details={
                "unsupported_claims": [],
                "supported_claims": [],
                "certainty": "certain",
            },
        )

    supported, unsupported = supported_claims(
        claims,
        context,
    )

    score = round(
        10 * len(supported) / max(len(claims), 1),
        2,
    )

    return EvaluationResult(
        score=score,
        explanation=(
            "Rule-based groundedness estimate based on claim "
            "support in the supplied or retrieved evidence."
        ),
        details={
            "unsupported_claims": unsupported,
            "supported_claims": supported,
            "certainty": "certain",
        },
    )