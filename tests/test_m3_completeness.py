from evaluation.completeness import evaluate_completeness


def test_fully_complete_response():
    result = evaluate_completeness(
        question="What is a microprocessor?",
        ai_response=(
            "A microprocessor is an integrated circuit that "
            "contains the functions of a central processing unit. "
            "It performs arithmetic, logical, and control operations."
        ),
        reference_answer=(
            "A microprocessor is an integrated circuit that contains "
            "the functions of a central processing unit. "
            "It performs arithmetic and logical operations."
        ),
    )

    assert result.score >= 9.0
    assert result.details["addressed_aspects"]
    assert result.details["missing_aspects"] == []
    assert result.details["reasoning"]


def test_partially_complete_response():
    result = evaluate_completeness(
        question="What is a microprocessor?",
        ai_response=(
            "A microprocessor is an integrated circuit that "
            "contains the functions of a central processing unit."
        ),
        reference_answer=(
            "A microprocessor is an integrated circuit that contains "
            "the functions of a central processing unit. "
            "It performs arithmetic and logical operations."
        ),
    )

    assert 4.0 <= result.score < 9.0
    assert result.details["addressed_aspects"]
    assert (
        result.details["partial_aspects"]
        or result.details["missing_aspects"]
    )
    assert result.details["reasoning"]


def test_substantially_incomplete_response():
    result = evaluate_completeness(
        question="What is a microprocessor?",
        ai_response="It is a device.",
        reference_answer=(
            "A microprocessor is an integrated circuit that contains "
            "the functions of a central processing unit. "
            "It performs arithmetic and logical operations."
        ),
    )

    assert result.score < 4.0
    assert result.details["missing_aspects"]
    assert result.details["reasoning"]


def test_no_reference_uses_baseline():
    result = evaluate_completeness(
        question="What is a microprocessor?",
        ai_response="A microprocessor is used for processing data.",
    )

    assert result.score == 8.0
    assert result.details["target"] == "question"
    assert result.details["addressed_aspects"]
    assert result.details["missing_aspects"] == []