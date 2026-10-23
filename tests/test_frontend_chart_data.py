import pandas as pd
import pytest

from frontend.chart_data import batch_chart_data, hallucination_status, single_score_data


def test_single_score_data_uses_only_available_numeric_metrics():
    scores = single_score_data(
        {
            "relevance": {"score": 8.5},
            "factuality": {"score": "7"},
            "completeness": {"score": None},
            "hallucination": {
                "hallucination_detected": True,
                "certainty": "certain",
            },
        }
    )

    assert scores["Score"].to_dict() == {
        "Relevance": 8.5,
        "Accuracy (Factuality)": 7.0,
    }
    assert hallucination_status(
        {"hallucination": {"hallucination_detected": True, "certainty": "certain"}}
    ) == "Detected"


def test_single_score_data_accepts_a_returned_hallucination_score():
    scores = single_score_data(
        {
            "relevance": {"score": 8},
            "accuracy_score": 7,
            "completeness_score": 9,
            "hallucination_score": 2,
        }
    )

    assert scores["Score"].to_dict() == {
        "Relevance": 8.0,
        "Accuracy (Factuality)": 7.0,
        "Completeness": 9.0,
        "Hallucination": 2.0,
    }


def test_batch_chart_data_produces_per_response_scores_and_summaries():
    results = pd.DataFrame(
        [
            {
                "Record": 1,
                "Relevance": 8,
                "Factuality": 6,
                "Completeness": 10,
                "Hallucination": "Detected",
                "Verdict": "PASS",
            },
            {
                "Record": 2,
                "Relevance": None,
                "Factuality": 4,
                "Completeness": 6,
                "Hallucination": "Not Detected",
                "Verdict": "NEEDS IMPROVEMENT",
            },
            {
                "Record": 3,
                "Relevance": None,
                "Factuality": None,
                "Completeness": None,
                "Hallucination": "Uncertain",
                "Verdict": "FAIL",
            },
            {
                "Record": 4,
                "Relevance": None,
                "Factuality": None,
                "Completeness": None,
                "Hallucination": None,
                "Verdict": "ERROR",
            },
        ]
    )

    response_scores, verdict_counts, averages = batch_chart_data(results)

    assert response_scores["Response"].tolist() == ["1", "2"]
    assert response_scores.loc[0, "Accuracy (Factuality)"] == 6
    assert response_scores.loc[1, "Accuracy (Factuality)"] == 4
    assert "Hallucination" not in response_scores.columns
    assert verdict_counts.set_index("Verdict")["Count"].to_dict() == {
        "PASS": 1,
        "NEEDS IMPROVEMENT": 1,
        "FAIL": 1,
    }
    assert averages.loc["Accuracy (Factuality)", "Average Score"] == pytest.approx(5)


def test_batch_chart_data_handles_missing_or_invalid_scores():
    results = pd.DataFrame(
        [
            {"Record": 1, "Relevance": float("nan"), "Verdict": "PASS"},
            {"Record": 2, "Relevance": 11, "Verdict": None},
            {"Record": 3, "Relevance": "not a score", "Verdict": "ERROR"},
        ]
    )

    response_scores, verdict_counts, averages = batch_chart_data(results)

    assert response_scores.empty
    assert averages.empty
    assert verdict_counts.set_index("Verdict").loc["PASS", "Count"] == 1
    assert single_score_data({"relevance": {"score": float("inf")}}).empty
    assert hallucination_status(
        {"hallucination": {"hallucination_detected": None, "certainty": "uncertain"}}
    ) == "Uncertain"
