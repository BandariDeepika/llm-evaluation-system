from evaluation.common import EvaluationResult, clamp_score, tokenize


def evaluate_relevance(question: str, ai_response: str) -> EvaluationResult:
    """Estimate relevance using question-term coverage and response usefulness."""

    if not question.strip() or not ai_response.strip():
        raise ValueError("question and ai_response must contain text")

    question_words = tokenize(question)
    response_words = tokenize(ai_response)

    matched_terms = len(question_words & response_words)
    coverage = matched_terms / max(len(question_words), 1)

    # Short direct answers can be relevant even when they do not
    # repeat the words from the question.
    if len(response_words) <= 10 and ai_response.strip():
        score = max(coverage * 10, 8.0)
    else:
        score = coverage * 10

    score = clamp_score(score)

    return EvaluationResult(
        score=score,
        explanation=(
            "Rule-based relevance estimate using question-term coverage "
            "with support for short direct answers."
        ),
        details={
            "question_terms": len(question_words),
            "matched_terms": matched_terms,
        },
    )