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
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if token not in {"a", "an", "and", "the", "is", "of", "to", "in", "it"}
    }


def split_claims(text: str) -> list[str]:
    """Split a response into non-empty sentence-like claims."""
    return [claim.strip() for claim in re.split(r"(?<=[.!?])\s+|\n+", text) if claim.strip()]


def supported_claims(claims: Iterable[str], evidence: str) -> tuple[list[str], list[str]]:
    """Classify claims using word overlap; intended as a pre-LLM baseline."""
    evidence_words = tokenize(evidence)
    evidence_named_words = set(re.findall(r"\b[A-Z][a-z]+\b", evidence))
    supported: list[str] = []
    unsupported: list[str] = []
    for claim in claims:
        claim_words = tokenize(claim)
        overlap = len(claim_words & evidence_words) / max(len(claim_words), 1)
        claim_named_words = set(re.findall(r"\b[A-Z][a-z]+\b", claim))
        conflicting_named_words = claim_named_words - evidence_named_words
        if overlap >= 0.5 and not (evidence_named_words and conflicting_named_words):
            supported.append(claim)
        else:
            unsupported.append(claim)
    return supported, unsupported


def clamp_score(score: float) -> float:
    return round(max(0.0, min(10.0, score)), 2)