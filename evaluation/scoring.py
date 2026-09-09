from collections.abc import Mapping
from typing import Optional, Union

from evaluation.common import EvaluationResult, clamp_score


DEFAULT_WEIGHTS: dict[str, float] = {
    "relevance": 0.20,
    "factuality": 0.25,
    "faithfulness": 0.25,
    "completeness": 0.15,
    "semantic_similarity": 0.15,
}


def calculate_overall_score(
    results: Mapping[str, Union[EvaluationResult, Optional[float]]],
    weights: Optional[Mapping[str, float]] = None, 
) -> EvaluationResult:
    """Compute a weighted mean after removing unavailable dimensions."""
    selected_weights = dict(weights or DEFAULT_WEIGHTS)
    available = {
        name: result.score if isinstance(result, EvaluationResult) else result
        for name, result in results.items()
        if (result.score if isinstance(result, EvaluationResult) else result) is not None
        and name in selected_weights
    }
    if not available:
        return EvaluationResult(score=None, explanation="Overall score is unavailable because no evaluation dimensions produced a score.", details={"used_dimensions": []})
    total_weight = sum(selected_weights[name] for name in available)
    score = sum(float(value) * selected_weights[name] for name, value in available.items()) / total_weight
    return EvaluationResult(
        score=clamp_score(score),
        explanation="Weighted mean of available evaluation dimensions; unavailable dimensions are excluded and the remaining weights are renormalized.",
        details={"used_dimensions": list(available), "weights": {name: selected_weights[name] / total_weight for name in available}},
    )