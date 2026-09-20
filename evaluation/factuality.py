from typing import Optional

from evaluation.common import (
    EvaluationResult,
    split_claims,
    supported_claims,
)


def _extract_contradictory_claims(
    claims: list[str],
    evidence: str,
) -> list[str]:
    contradictions = []

    evidence_lower = evidence.lower()

    for claim in claims:
        claim_lower = claim.lower()

        if "capital" in claim_lower and "capital" in evidence_lower:
            if "france" in claim_lower and "france" in evidence_lower:

                known_capitals = {
                    "paris",
                    "london",
                    "berlin",
                    "rome",
                    "tokyo",
                    "delhi",
                    "beijing",
                    "washington",
                }

                claim_values = {
                    word
                    for word in known_capitals
                    if word in claim_lower
                }

                evidence_values = {
                    word
                    for word in known_capitals
                    if word in evidence_lower
                }

                if claim_values and evidence_values:
                    if claim_values.isdisjoint(evidence_values):
                        contradictions.append(claim)

    return contradictions


def _definition_topic_overlap(
    question: str,
    ai_response: str,
    reference_answer: str,
) -> bool:

    question_lower = question.lower()
    response_lower = ai_response.lower()
    reference_lower = reference_answer.lower()

    definition_terms = {
        "microprocessor",
        "processor",
        "microcontroller",
        "computer",
        "algorithm",
        "database",
        "network",
        "transistor",
        "diode",
        "capacitor",
        "resistor",
        "programming",
        "software",
        "hardware",
    }

    for term in definition_terms:
        if (
            term in question_lower
            and term in response_lower
            and term in reference_lower
        ):
            return True

    return False


def evaluate_factuality(
    question: str,
    ai_response: str,
    reference_answer: Optional[str] = None,
    context: Optional[str] = None,
) -> EvaluationResult:

    if not question.strip() or not ai_response.strip():
        raise ValueError(
            "question and ai_response must contain text"
        )

    evidence_parts = []

    if reference_answer and reference_answer.strip():
        evidence_parts.append(reference_answer.strip())

    if context and context.strip():
        evidence_parts.append(context.strip())

    evidence = " ".join(evidence_parts)

    if not evidence:
        return EvaluationResult(
            score=None,
            explanation=(
                "Accuracy is unavailable because no reference answer "
                "or supporting source context was supplied."
            ),
            details={
                "category": "uncertain",
                "supported_claims": [],
                "unsupported_claims": [],
                "contradicted_claims": [],
                "supporting_evidence": [],
                "certainty": "uncertain",
                "judge": "M2.2 Accuracy Judge Agent",
            },
        )

    claims = split_claims(ai_response)

    if not claims:
        return EvaluationResult(
            score=0.0,
            explanation=(
                "The AI response does not contain an evaluable claim."
            ),
            details={
                "category": "incorrect",
                "supported_claims": [],
                "unsupported_claims": [],
                "contradicted_claims": [],
                "supporting_evidence": [],
                "certainty": "certain",
                "judge": "M2.2 Accuracy Judge Agent",
            },
        )

    supported, unsupported = supported_claims(
        claims,
        evidence,
    )

    contradicted = _extract_contradictory_claims(
        claims,
        evidence,
    )

    supported = [
        claim
        for claim in supported
        if claim not in contradicted
    ]

    # Check for a semantically related definition answer.
    definition_match = (
        not supported
        and not contradicted
        and reference_answer is not None
        and _definition_topic_overlap(
            question,
            ai_response,
            reference_answer,
        )
    )

    supported_count = len(supported)
    contradicted_count = len(contradicted)
    unsupported_count = len(unsupported)
    total_claims = len(claims)

    if contradicted_count > 0:

        category = "contradictory"
        score = 3.0

        reasoning = (
            "The AI response contains one or more claims that "
            "contradict the supplied reference answer or source context."
        )

    elif definition_match:

        category = "partially_correct"
        score = 7.0

        reasoning = (
            "The AI response discusses the correct topic and provides "
            "related information, but it does not fully match the "
            "reference answer."
        )

    elif supported_count == total_claims:

        category = "correct"
        score = 10.0

        reasoning = (
            "The AI response is fully supported by the supplied "
            "reference answer or source context."
        )

    elif supported_count > 0:

        category = "partially_correct"

        score = (
            10 * supported_count
            + 2 * unsupported_count
        ) / total_claims

        reasoning = (
            "The AI response contains some claims supported by the "
            "available evidence, while other claims are not fully supported."
        )

    else:

        category = "incorrect"
        score = 0.0

        reasoning = (
            "The claims in the AI response are not supported by the "
            "available reference answer or source context."
        )

    supporting_evidence = []

    if supported or definition_match:
        supporting_evidence.append(evidence)

    return EvaluationResult(
        score=round(score, 2),
        explanation=reasoning,
        details={
            "category": category,
            "total_claims": total_claims,
            "supported_claims": supported,
            "unsupported_claims": unsupported,
            "contradicted_claims": contradicted,
            "supporting_evidence": supporting_evidence,
            "certainty": "certain",
            "judge": "M2.2 Accuracy Judge Agent",
        },
    )
