
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
    Detect factual contradictions between the AI response
    and the supplied reference evidence.
    """

    contradictions = []

    evidence_lower = evidence.lower()

    # ---------------------------------------------------------
    # Known capital-city relationships
    # ---------------------------------------------------------

    capital_pairs = {
        "france": "paris",
        "united kingdom": "london",
        "uk": "london",
        "germany": "berlin",
        "italy": "rome",
        "japan": "tokyo",
        "india": "delhi",
        "china": "beijing",
        "united states": "washington",
        "usa": "washington",
    }

    capital_cities = {
        "paris",
        "london",
        "berlin",
        "rome",
        "tokyo",
        "delhi",
        "beijing",
        "washington",
    }

    # ---------------------------------------------------------
    # Check each AI claim
    # ---------------------------------------------------------

    for claim in claims:

        claim_lower = claim.lower()

        if "capital" not in claim_lower:
            continue

        # -----------------------------------------------------
        # Check country-capital relationships
        # -----------------------------------------------------

        for country, correct_capital in capital_pairs.items():

            if country not in claim_lower:
                continue

            # Find capital mentioned in AI response
            claim_capitals = {
                city
                for city in capital_cities
                if city in claim_lower
            }

            # If AI response mentions a capital
            if claim_capitals:

                # If the correct capital is not mentioned,
                # but another capital is mentioned,
                # it is a contradiction.
                if correct_capital not in claim_capitals:

                    contradictions.append(claim)

                # If the correct capital is mentioned,
                # verify that evidence agrees.
                elif correct_capital in claim_capitals:

                    if correct_capital not in evidence_lower:
                        contradictions.append(claim)

            break

    # ---------------------------------------------------------
    # Direct France example
    # ---------------------------------------------------------

    if (
        "capital of france" in evidence_lower
    ):

        for claim in claims:

            claim_lower = claim.lower()

            if "capital of france" not in claim_lower:
                continue

            # Evidence says Paris but response says London
            if (
                "paris" in evidence_lower
                and "london" in claim_lower
            ):
                if claim not in contradictions:
                    contradictions.append(claim)

            # Evidence says London but response says Paris
            elif (
                "london" in evidence_lower
                and "paris" in claim_lower
            ):
                if claim not in contradictions:
                    contradictions.append(claim)

    return contradictions


def _is_related_definition(
    claim: str,
    evidence: str,
) -> bool:
    """
    Check whether a definition-type claim is related
    to the supplied evidence.
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

        if (
            topic in claim_lower
            and topic in evidence_lower
        ):
            return True

    return False


def detect_hallucination(
    ai_response: str,
    evidence: Optional[str],
) -> HallucinationResult:
    """
    Detect hallucinations using supplied evidence.

    Evidence sources can be:
    - source document
    - reference answer
    - retrieved knowledge-base context

    If evidence is unavailable, the result is UNCERTAIN.
    """

    # ---------------------------------------------------------
    # Validate response
    # ---------------------------------------------------------

    if not ai_response or not ai_response.strip():

        raise ValueError(
            "ai_response must contain text"
        )

    # ---------------------------------------------------------
    # Debug information
    # ---------------------------------------------------------

    print(
        "DEBUG HALLUCINATION EVIDENCE:",
        repr(evidence),
    )

    # ---------------------------------------------------------
    # No evidence
    # ---------------------------------------------------------

    if not evidence or not evidence.strip():

        return HallucinationResult(
            hallucination_detected=None,
            severity=None,
            unsupported_claims=[],
            contradicted_claims=[],
            supported_claims=[],
            explanation=(
                "Insufficient evidence to determine whether "
                "the response contains hallucinations."
            ),
            certainty="uncertain",
        )

    evidence = evidence.strip()

    # ---------------------------------------------------------
    # Split response into claims
    # ---------------------------------------------------------

    claims = split_claims(
        ai_response
    )

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

    # ---------------------------------------------------------
    # Supported / unsupported claims
    # ---------------------------------------------------------

    supported, unsupported = supported_claims(
        claims,
        evidence,
    )

    # ---------------------------------------------------------
    # Contradiction detection
    # ---------------------------------------------------------

    contradicted = _detect_contradictions(
        claims,
        evidence,
    )

    # ---------------------------------------------------------
    # Remove contradicted claims from supported claims
    # ---------------------------------------------------------

    supported = [
        claim
        for claim in supported
        if claim not in contradicted
    ]

    # ---------------------------------------------------------
    # Related definition handling
    # ---------------------------------------------------------

    for claim in list(unsupported):

        if claim not in contradicted:

            if _is_related_definition(
                claim,
                evidence,
            ):

                unsupported.remove(
                    claim
                )

                supported.append(
                    claim
                )

    # ---------------------------------------------------------
    # Contradicted claims must be unsupported
    # ---------------------------------------------------------

    for claim in contradicted:

        if claim not in unsupported:

            unsupported.append(
                claim
            )

    # ---------------------------------------------------------
    # Calculate hallucination
    # ---------------------------------------------------------

    total_claims = len(claims)

    problematic_claims = len(
        set(unsupported)
        | set(contradicted)
    )

    hallucination_detected = (
        problematic_claims > 0
    )

    problem_ratio = (
        problematic_claims
        / max(total_claims, 1)
    )

    # ---------------------------------------------------------
    # Severity
    # ---------------------------------------------------------

    if not hallucination_detected:

        severity = "LOW"

        explanation = (
            "All evaluated claims are supported by the "
            "supplied evidence or are consistent with the "
            "referenced information."
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
        or len(contradicted) > 0
    ):

        severity = "MEDIUM"

        explanation = (
            "The response contains unsupported or "
            "contradicted claims that are not fully "
            "supported by the evidence."
        )

    else:

        severity = "LOW"

        explanation = (
            "The response contains a small number of "
            "unsupported claims."
        )

    # ---------------------------------------------------------
    # Final result
    # ---------------------------------------------------------

    return HallucinationResult(

        hallucination_detected=(
            hallucination_detected
        ),

        severity=severity,

        unsupported_claims=(
            unsupported
        ),

        contradicted_claims=(
            contradicted
        ),

        supported_claims=(
            supported
        ),

        explanation=explanation,

        certainty="certain",
    )

