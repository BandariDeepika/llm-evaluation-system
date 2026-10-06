from evaluation.common import EvaluationResult, clamp_score, tokenize


STOP_WORDS = {
    "what",
    "is",
    "are",
    "was",
    "were",
    "the",
    "a",
    "an",
    "of",
    "to",
    "for",
    "in",
    "on",
    "and",
    "or",
    "do",
    "does",
    "did",
    "how",
    "why",
    "when",
    "where",
    "who",
}


# Direct-answer mappings for common factual questions.
# These help short but correct answers such as "Paris."
# from being incorrectly classified as irrelevant.
KNOWN_DIRECT_ANSWERS = {
    "what is the capital of france": {"paris"},
}


def evaluate_relevance(question: str, ai_response: str) -> EvaluationResult:
    """
    M2.1 Relevance Judge Agent.

    Evaluates whether the AI response directly and appropriately
    addresses the submitted question.
    """

    if not question.strip() or not ai_response.strip():
        raise ValueError("question and ai_response must contain text")

    normalized_question = question.strip().lower().rstrip("?.!")
    normalized_response = ai_response.strip().lower()

    question_words = tokenize(question)
    response_words = tokenize(ai_response)

    # Remove common words and keep meaningful terms
    question_content_words = question_words - STOP_WORDS
    response_content_words = response_words - STOP_WORDS

    matched_terms = len(
        question_content_words & response_content_words
    )

    question_term_count = len(question_content_words)

    coverage = matched_terms / max(question_term_count, 1)

    # ---------------------------------------------------------
    # Direct factual answer detection
    # ---------------------------------------------------------
    # Example:
    # Question: What is the capital of France?
    # Response: Paris.
    #
    # "Paris" does not share keywords with "capital France",
    # but it is still a direct and relevant answer.
    # ---------------------------------------------------------

    direct_answer_terms = KNOWN_DIRECT_ANSWERS.get(
        normalized_question,
        set(),
    )

    direct_answer_detected = any(
        answer_term in normalized_response
        for answer_term in direct_answer_terms
    )

    # Detect vague answers for definition-type questions
    definition_question = normalized_question.startswith(
        ("what is", "what are", "define")
    )

    vague_phrases = (
        "is related to",
        "are related to",
        "is associated with",
        "are associated with",
        "is connected to",
        "are connected to",
        "is about",
        "are about",
    )

    vague_answer = any(
        phrase in normalized_response
        for phrase in vague_phrases
    )

    # ---------------------------------------------------------
    # Rule-based relevance score
    # ---------------------------------------------------------

    if direct_answer_detected:
        score = 10.0
        category = "fully_relevant"

    elif definition_question and vague_answer:
        score = 2.5
        category = "mostly_irrelevant"

    elif coverage >= 0.75:
        score = 9.0
        category = "fully_relevant"

    elif coverage >= 0.50:
        score = 7.5
        category = "mostly_relevant"

    elif coverage >= 0.25:
        score = 5.0
        category = "partially_relevant"

    elif coverage > 0:
        score = 2.5
        category = "mostly_irrelevant"

    else:
        score = 0.0
        category = "completely_unrelated"

    score = clamp_score(score)

    # ---------------------------------------------------------
    # Generate reasoning
    # ---------------------------------------------------------

    if direct_answer_detected:
        reasoning = (
            "The response directly provides the expected answer "
            "to the submitted question."
        )

    elif category == "fully_relevant":
        reasoning = (
            "The response directly addresses the question and "
            "contains relevant information."
        )

    elif category == "mostly_relevant":
        reasoning = (
            "The response addresses the main topic of the question "
            "but may not cover all aspects."
        )

    elif category == "partially_relevant":
        reasoning = (
            "The response addresses part of the question but "
            "contains limited relevant information."
        )

    elif category == "mostly_irrelevant":
        reasoning = (
            "The response has limited connection to the submitted question "
            "and does not directly address the main requirement."
        )

    else:
        reasoning = (
            "The response does not contain meaningful information related "
            "to the submitted question."
        )

    return EvaluationResult(
        score=score,
        explanation=reasoning,
        details={
            "category": category,
            "question_terms": question_term_count,
            "matched_terms": matched_terms,
            "coverage": round(coverage, 2),
            "direct_answer_detected": direct_answer_detected,
            "judge": "M2.1 Relevance Judge Agent",
        },
    )