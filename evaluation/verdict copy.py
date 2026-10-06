from typing import Literal, Optional

from pydantic import BaseModel, Field

from evaluation.common import EvaluationResult
from evaluation.hallucination import HallucinationResult


# M3.2 weighted evaluation model
#
# Accuracy and hallucination are given higher importance because
# factual correctness and unsupported claims are critical to
# overall response quality.
#
# The weights total 1.00.

VERDICT_WEIGHTS = {
    "relevance": 0.20,
    "factuality": 0.35,
    "completeness": 0.20,
    "hallucination": 0.25,
}


class VerdictResult(BaseModel):
    """Structured final verdict generated from evaluation dimensions."""

    overall_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=10,
    )

    verdict: Literal[
        "PASS",
        "NEEDS IMPROVEMENT",
        "FAIL",
    ]

    major_issues: list[str] = Field(
        default_factory=list
    )

    consolidated_reasoning: str

    weights: dict[str, float] = Field(
        default_factory=dict
    )


def _hallucination_score(
    hallucination: HallucinationResult,
) -> Optional[float]:
    """
    Convert hallucination status into a 0-10 quality score.

    No detected hallucination receives the maximum score.
    Severity reduces the score according to the level of risk.
    """

    if hallucination.hallucination_detected is None:
        return None

    if not hallucination.hallucination_detected:
        return 10.0

    severity_scores = {
        "LOW": 7.0,
        "MEDIUM": 4.0,
        "HIGH": 0.0,
    }

    return severity_scores.get(
        hallucination.severity,
        0.0,
    )


def calculate_verdict(
    relevance: EvaluationResult,
    factuality: EvaluationResult,
    completeness: EvaluationResult,
    hallucination: HallucinationResult,
) -> VerdictResult:
    """Calculate the M3.2 weighted score and final quality verdict."""

    dimension_scores = {
        "relevance": relevance.score,
        "factuality": factuality.score,
        "completeness": completeness.score,
        "hallucination": _hallucination_score(
            hallucination
        ),
    }

    available = {
        name: score
        for name, score in dimension_scores.items()
        if score is not None
    }

    if not available:
        return VerdictResult(
            overall_score=None,
            verdict="FAIL",
            major_issues=[
                "No evaluation dimension produced a usable score."
            ],
            consolidated_reasoning=(
                "A final verdict could not be supported because "
                "the required evaluation dimensions were unavailable."
            ),
            weights={},
        )

    total_weight = sum(
        VERDICT_WEIGHTS[name]
        for name in available
    )

    overall_score = sum(
        float(score) * VERDICT_WEIGHTS[name]
        for name, score in available.items()
    ) / total_weight

    overall_score = round(
        max(0.0, min(10.0, overall_score)),
        2,
    )

    major_issues: list[str] = []

    # ---------------------------------------------------------
    # Identify important quality problems
    # ---------------------------------------------------------

    if factuality.score is not None and factuality.score < 7:
        major_issues.append(
            "The response contains factual inaccuracies "
            "or incomplete factual information."
        )

    if completeness.score is not None and completeness.score < 7:
        major_issues.append(
            "The response does not fully address all expected "
            "information."
        )

    if relevance.score is not None and relevance.score < 7:
        major_issues.append(
            "The response does not fully address the submitted question."
        )

    if hallucination.hallucination_detected:
        severity = hallucination.severity or "UNKNOWN"

        major_issues.append(
            f"Hallucination risk detected at {severity} severity."
        )

    # ---------------------------------------------------------
    # Critical failure conditions
    # ---------------------------------------------------------

    critical_hallucination = (
        hallucination.hallucination_detected is True
        and hallucination.severity == "HIGH"
    )

    factual_contradiction = (
        factuality.details.get("category") == "contradictory"
    )

    if critical_hallucination or factual_contradiction:
        verdict = "FAIL"

    elif overall_score >= 8.0:
        verdict = "PASS"

    elif overall_score >= 5.0:
        verdict = "NEEDS IMPROVEMENT"

    else:
        verdict = "FAIL"

    # ---------------------------------------------------------
    # Consolidated reasoning
    # ---------------------------------------------------------

    if verdict == "PASS":
        consolidated_reasoning = (
            "The response demonstrates strong overall quality "
            "across relevance, factuality, completeness, and "
            "hallucination checks. No critical evaluation issue "
            "was identified."
        )

    elif verdict == "NEEDS IMPROVEMENT":
        consolidated_reasoning = (
            "The response is partially acceptable but has one or "
            "more areas that require improvement. The weighted "
            "evaluation indicates that the response should be "
            "reviewed before being considered fully reliable."
        )

    else:
        consolidated_reasoning = (
            "The response contains significant quality issues "
            "that prevent it from being considered reliable. "
            "Critical factual or hallucination problems may "
            "override the weighted score."
        )

    return VerdictResult(
        overall_score=overall_score,
        verdict=verdict,
        major_issues=major_issues,
        consolidated_reasoning=consolidated_reasoning,
        weights={
            name: VERDICT_WEIGHTS[name]
            for name in available
        },
    )