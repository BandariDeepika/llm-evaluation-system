from typing import Literal, Optional
from pydantic import BaseModel, Field

from evaluation.common import split_claims, supported_claims


class HallucinationResult(BaseModel):
    hallucination_detected: Optional[bool]
    severity: Optional[Literal["LOW", "MEDIUM", "HIGH"]]
    unsupported_claims: list[str] = Field(default_factory=list)
    explanation: str
    certainty: Literal["certain", "uncertain"]


def detect_hallucination(ai_response: str, evidence: Optional[str]) -> HallucinationResult:
    """Detect unsupported claims when evidence exists; otherwise report uncertainty."""
    if not evidence or not evidence.strip():
        return HallucinationResult(
            hallucination_detected=None,
            severity=None,
            explanation="Insufficient evidence to determine whether the response contains hallucinations.",
            certainty="uncertain",
        )
    _, unsupported = supported_claims(split_claims(ai_response), evidence)
    if not unsupported:
        return HallucinationResult(
            hallucination_detected=False,
            severity="LOW",
            unsupported_claims=[],
            explanation="All sentence-like claims met the baseline evidence-overlap rule.",
            certainty="certain",
        )
    ratio = len(unsupported) / max(len(split_claims(ai_response)), 1)
    severity = "HIGH" if ratio >= 0.75 else "MEDIUM" if ratio >= 0.4 else "LOW"
    return HallucinationResult(
        hallucination_detected=True,
        severity=severity,
        unsupported_claims=unsupported,
        explanation="One or more claims were not supported by the supplied evidence; this baseline cannot reliably identify contradictions.",
        certainty="certain",
    )