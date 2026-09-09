import pytest
from pydantic import ValidationError

from evaluation.completeness import evaluate_completeness
from evaluation.common import EvaluationResult
from evaluation.hallucination import detect_hallucination
from evaluation.relevance import evaluate_relevance
from evaluation.scoring import calculate_overall_score


def test_semantic_similarity_matches_paraphrases() -> None:
    pytest.importorskip("sentence_transformers")
    from evaluation.semantic_similarity import evaluate_semantic_similarity

    result = evaluate_semantic_similarity(
        "Paris is the capital of France.",
        "The capital city of France is Paris.",
    )

    assert result.details["similarity"] > 0.7
    assert result.score is not None and result.score > 8


def test_semantic_similarity_distinguishes_different_facts() -> None:
    pytest.importorskip("sentence_transformers")
    from evaluation.semantic_similarity import evaluate_semantic_similarity

    result = evaluate_semantic_similarity(
        "Paris is the capital of France.",
        "Berlin is the capital of Germany.",
    )

    assert result.details["similarity"] < 0.8


def test_semantic_similarity_is_unavailable_without_reference() -> None:
    pytest.importorskip("sentence_transformers")
    from evaluation.semantic_similarity import evaluate_semantic_similarity

    result = evaluate_semantic_similarity("An answer", None)

    assert result.score is None
    assert result.details["certainty"] == "unavailable"


def test_scoring_renormalizes_available_weights() -> None:
    results = {
        "relevance": EvaluationResult(score=8, explanation="relevant"),
        "factuality": EvaluationResult(score=6, explanation="supported"),
        "faithfulness": None,
        "completeness": EvaluationResult(score=10, explanation="complete"),
        "semantic_similarity": None,
    }

    result = calculate_overall_score(results)

    assert result.score == pytest.approx((8 * 0.20 + 6 * 0.25 + 10 * 0.15) / 0.60, abs=0.01)
    assert result.details["used_dimensions"] == ["relevance", "factuality", "completeness"]


def test_hallucination_is_uncertain_without_evidence() -> None:
    result = detect_hallucination("Paris is the capital of France.", None)

    assert result.hallucination_detected is None
    assert result.severity is None
    assert result.certainty == "uncertain"


def test_hallucination_marks_unsupported_claims() -> None:
    result = detect_hallucination(
        "Berlin is the capital of France.",
        "Paris is the capital of France.",
    )

    assert result.hallucination_detected is True
    assert result.severity in {"LOW", "MEDIUM", "HIGH"}
    assert result.unsupported_claims


def test_empty_inputs_are_rejected() -> None:
    with pytest.raises(ValueError):
        evaluate_relevance(" ", "An answer")
    with pytest.raises(ValueError):
        evaluate_completeness("A question", " ")


def test_evaluation_result_rejects_out_of_range_score() -> None:
    with pytest.raises(ValidationError):
        EvaluationResult(score=11, explanation="invalid")