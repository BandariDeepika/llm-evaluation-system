from typing import Optional

from evaluation.common import EvaluationResult
from evaluation.hallucination import HallucinationResult
from evaluation.verdict import calculate_verdict


def make_result(
    score: float,
    category: str = "correct",
) -> EvaluationResult:
    """Create a simple evaluation result for verdict testing."""

    return EvaluationResult(
        score=score,
        explanation="Test evaluation result.",
        details={
            "category": category,
        },
    )


def make_hallucination(
    detected: bool,
    severity: Optional[str] = None,
) -> HallucinationResult:
    """Create a hallucination result for verdict testing."""

    return HallucinationResult(
        hallucination_detected=detected,
        severity=severity,
        unsupported_claims=[],
        contradicted_claims=[],
        supported_claims=[],
        explanation="Test hallucination result.",
        certainty="certain",
    )


def test_strong_response_returns_pass():
    result = calculate_verdict(
        relevance=make_result(9.0),
        factuality=make_result(9.5),
        completeness=make_result(9.0),
        hallucination=make_hallucination(
            detected=False,
            severity="LOW",
        ),
    )

    assert result.overall_score >= 8.0
    assert result.verdict == "PASS"
    assert result.major_issues == []
    assert result.consolidated_reasoning


def test_moderate_response_needs_improvement():
    result = calculate_verdict(
        relevance=make_result(7.0),
        factuality=make_result(6.0),
        completeness=make_result(6.0),
        hallucination=make_hallucination(
            detected=False,
            severity="LOW",
        ),
    )

    assert 5.0 <= result.overall_score < 8.0
    assert result.verdict == "NEEDS IMPROVEMENT"
    assert result.major_issues
    assert result.consolidated_reasoning


def test_low_score_response_returns_fail():
    result = calculate_verdict(
        relevance=make_result(3.0),
        factuality=make_result(2.0),
        completeness=make_result(3.0),
        hallucination=make_hallucination(
            detected=True,
            severity="MEDIUM",
        ),
    )

    assert result.overall_score < 5.0
    assert result.verdict == "FAIL"
    assert result.major_issues
    assert result.consolidated_reasoning


def test_contradictory_factuality_forces_fail():
    result = calculate_verdict(
        relevance=make_result(9.0),
        factuality=make_result(
            3.0,
            category="contradictory",
        ),
        completeness=make_result(9.0),
        hallucination=make_hallucination(
            detected=True,
            severity="MEDIUM",
        ),
    )

    assert result.verdict == "FAIL"
    assert result.overall_score is not None
    assert result.major_issues


def test_high_hallucination_forces_fail():
    result = calculate_verdict(
        relevance=make_result(10.0),
        factuality=make_result(10.0),
        completeness=make_result(10.0),
        hallucination=make_hallucination(
            detected=True,
            severity="HIGH",
        ),
    )

    assert result.overall_score is not None
    assert result.verdict == "FAIL"
    assert any(
        "Hallucination" in issue
        for issue in result.major_issues
    )