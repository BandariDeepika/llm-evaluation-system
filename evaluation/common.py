import re
from typing import Iterable, Optional

from pydantic import BaseModel, Field


class EvaluationResult(BaseModel):
    """Common structured output returned by an evaluation module."""

    score: Optional[float] = Field(default=None, ge=0, le=10)
    explanation: str
    details: dict[str, object] = Field(default_factory=dict)


def tokenize(text: str) -> set[str]:
    """Return normalized content words for simple, deterministic comparisons."""

    stop_words = {
        "a",
        "an",
        "and",
        "the",
        "is",
        "of",
        "to",
        "in",
        "it",
    }

    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token not in stop_words
    }


def split_claims(text: str) -> list[str]:
    """Split a response into non-empty sentence-like claims."""

    return [
        claim.strip()
        for claim in re.split(r"(?<=[.!?])\s+|\n+", text)
        if claim.strip()
    ]


def supported_claims(
    claims: Iterable[str],
    evidence: str,
) -> tuple[list[str], list[str]]:
    """
    Classify claims using deterministic word-overlap matching.

    A claim is considered supported when at least 50% of its
    important words are present in the supplied evidence.
    """

    evidence_words = tokenize(evidence)

    supported: list[str] = []
    unsupported: list[str] = []

    for claim in claims:
        claim_words = tokenize(claim)

        if not claim_words:
            unsupported.append(claim)
            continue

        # Calculate how much of the claim is present in the evidence.
        claim_coverage = len(
            claim_words & evidence_words
        ) / len(claim_words)

        # Classify the claim.
        if claim_coverage >= 0.5:
            supported.append(claim)
        else:
            unsupported.append(claim)

    return supported, unsupported


def clamp_score(score: float) -> float:
    """Keep score between 0 and 10."""

    return round(max(0.0, min(10.0, score)), 2)