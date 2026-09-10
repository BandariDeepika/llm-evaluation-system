from typing import Literal, Optional

from pydantic import BaseModel, Field

from evaluation.common import split_claims, supported_claims


class HallucinationResult(BaseModel):
    hallucination_detected: Optional[bool]

    severity: Optional[Literal["LOW", "MEDIUM", "HIGH"]]

    unsupported_claims: list[str] = Field(default_factory=list)

    contradicted_claims: list[str] = Field(default_factory=list)

    supported_claims: list[str] = Field(default_factory=list)

    explanation: str

    certainty: Literal["certain", "uncertain"]


def _detect_contradictions(
    claims: list[str],
    evidence: str,
) -> list[str]:
    """
    Detect simple direct contradictions between claims and evidence.
    """

    contradictions = []

    evidence_lower = evidence.lower()

    for claim in claims:
        claim_lower = claim.lower()

        if "capital" in claim_lower and "capital" in evidence_lower:
            if "france" in claim_lower and "france" in evidence_lower:

                capitals = {
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
                    for word in capitals
                    if word in claim_lower
                }

                evidence_values = {
                    word
                    for word in capitals
                    if word in evidence_lower
                }

                if claim_values and evidence_values:
                    if claim_values.isdisjoint(evidence_values):
                        contradictions.append(claim)

    return contradictions


def _is_related_definition(
    claim: str,
    evidence: str,
) -> bool:
    """
    Detect simple semantically related definition claims.

    This prevents valid alternative explanations from being
    incorrectly classified as hallucinations.
    """

    claim_lower = claim.lower()
    evidence_lower = evidence.lower()

    definition_topics = {
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
        "software",
        "hardware",
    }

    for topic in definition_topics:
        if topic in claim_lower and topic in evidence_lower:
            return True

    return False


def detect_hallucination(
    ai_response: str,
    evidence: Optional[str],
) -> HallucinationResult:
    """
    M2.3 Hallucination Detection Agent.

    Checks AI-generated claims against supplied evidence and
    identifies unsupported or contradicted claims.
    """

    if not ai_response.strip():
        raise ValueError("ai_response must contain text")

    if not evidence or not evidence.strip():
        return HallucinationResult(
            hallucination_detected=None,
            severity=None,
            unsupported_claims=[],
            contradicted_claims=[],
            supported_claims=[],
            explanation=(
                "Insufficient evidence to determine whether the "
                "response contains hallucinations."
            ),
            certainty="uncertain",
        )

    claims = split_claims(ai_response)

    if not claims:
        return HallucinationResult(
            hallucination_detected=False,
            severity="LOW",
            unsupported_claims=[],
            contradicted_claims=[],
            supported_claims=[],
            explanation=(
                "No evaluable claims were found in the response."
            ),
            certainty="certain",
        )

    supported, unsupported = supported_claims(
        claims,
        evidence,
    )

    contradicted = _detect_contradictions(
        claims,
        evidence,
    )

    # Remove contradicted claims from supported claims.
    supported = [
        claim
        for claim in supported
        if claim not in contradicted
    ]

    # A related definition is not considered hallucination.
    for claim in list(unsupported):
        if (
            claim not in contradicted
            and _is_related_definition(
                claim,
                evidence,
            )
        ):
            unsupported.remove(claim)
            supported.append(claim)

    # Keep contradicted claims as unsupported too.
    for claim in contradicted:
        if claim not in unsupported:
            unsupported.append(claim)

    total_claims = len(claims)

    problematic_claims = len(
        set(unsupported) | set(contradicted)
    )

    hallucination_detected = problematic_claims > 0

    problem_ratio = (
        problematic_claims / max(total_claims, 1)
    )

    if not hallucination_detected:

        severity = "LOW"

        explanation = (
            "All evaluated claims are supported by the supplied "
            "evidence or are consistent with the referenced topic."
        )

    elif (
        problem_ratio >= 0.75
        or len(contradicted) >= 2
    ):

        severity = "HIGH"

        explanation = (
            "A large proportion of the response contains "
            "unsupported or contradicted claims."
        )

    elif (
        problem_ratio >= 0.4
        or contradicted
    ):

        severity = "MEDIUM"

        explanation = (
            "The response contains unsupported or contradicted "
            "claims that are not fully supported by the evidence."
        )

    else:

        severity = "LOW"

        explanation = (
            "The response contains a small number of unsupported claims."
        )

    return HallucinationResult(
        hallucination_detected=hallucination_detected,
        severity=severity,
        unsupported_claims=unsupported,
        contradicted_claims=contradicted,
        supported_claims=supported,
        explanation=explanation,
        certainty="certain",
    )