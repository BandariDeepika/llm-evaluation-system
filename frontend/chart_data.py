"""Transform evaluator output into chart-ready, score-only data."""

import math
from typing import Any, Optional

import pandas as pd


SINGLE_SCORE_FIELDS: dict[str, tuple[str, ...]] = {
    "Relevance": ("relevance", "relevance_score"),
    "Accuracy (Factuality)": ("factuality", "accuracy", "factuality_score", "accuracy_score"),
    "Completeness": ("completeness", "completeness_score"),
    "Hallucination": ("hallucination_score", "hallucination"),
}

BATCH_SCORE_FIELDS: dict[str, tuple[str, ...]] = {
    "Relevance": ("Relevance",),
    "Accuracy (Factuality)": ("Factuality", "Accuracy"),
    "Faithfulness": ("Faithfulness",),
    "Completeness": ("Completeness",),
    "Semantic Similarity": ("Semantic Similarity",),
    "Overall Score": ("Overall Score",),
    "Weighted Score": ("Weighted Score",),
    "Hallucination": ("Hallucination Score", "Hallucination"),
}


def numeric_score(value: Any) -> Optional[float]:
    """Return finite evaluator scores in the supported 0-10 range."""
    if isinstance(value, dict):
        value = value.get("score")
    if value is None or isinstance(value, bool):
        return None
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(score) or not 0 <= score <= 10:
        return None
    return score


def single_score_data(result: dict[str, Any]) -> pd.DataFrame:
    """Build available Relevance, Accuracy, Completeness and Hallucination scores."""
    values = {}
    for label, fields in SINGLE_SCORE_FIELDS.items():
        for field in fields:
            score = numeric_score(result.get(field))
            if score is not None:
                values[label] = score
                break
    return pd.DataFrame({"Score": values})


def hallucination_status(result: dict[str, Any]) -> Optional[str]:
    """Return the evaluator's hallucination classification without inventing a score."""
    data = result.get("hallucination")
    if not isinstance(data, dict):
        return None
    if data.get("certainty") == "uncertain":
        return "Uncertain"
    detected = data.get("hallucination_detected")
    if detected is True:
        return "Detected"
    if detected is False:
        return "Not detected"
    if data.get("unsupported_claims"):
        return "Detected"
    return None


def batch_chart_data(
    results: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build per-response scores, verdict counts, and available score averages."""
    response_scores = pd.DataFrame()
    score_columns: dict[str, pd.Series] = {}

    for label, candidates in BATCH_SCORE_FIELDS.items():
        source_column = next((column for column in candidates if column in results.columns), None)
        if source_column is None:
            continue
        values = results[source_column].map(numeric_score)
        if values.notna().any():
            score_columns[label] = values

    if score_columns:
        score_frame = pd.DataFrame(score_columns, index=results.index)
        if "Record" in results.columns:
            records = results["Record"].map(lambda value: str(value))
        else:
            records = pd.Series(
                (str(index + 1) for index in range(len(results))),
                index=results.index,
            )
        response_scores = score_frame.copy()
        response_scores.insert(0, "Response", records)
        response_scores = response_scores.dropna(subset=list(score_columns), how="all")

    verdict_counts = pd.DataFrame(
        {"Verdict": ["PASS", "NEEDS IMPROVEMENT", "FAIL"], "Count": [0, 0, 0]}
    )
    if "Verdict" in results.columns:
        normalized = (
            results["Verdict"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
            .str.replace(r"[_-]+", " ", regex=True)
        )
        observed = normalized.value_counts()
        verdict_counts["Count"] = verdict_counts["Verdict"].map(observed).fillna(0).astype(int)

    averages = pd.DataFrame()
    if score_columns:
        averages = pd.DataFrame(
            {"Average Score": {label: values.mean() for label, values in score_columns.items()}}
        )

    return response_scores, verdict_counts, averages
