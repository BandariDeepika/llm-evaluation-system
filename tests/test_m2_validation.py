import json
from pathlib import Path

from evaluation.relevance import evaluate_relevance
from evaluation.factuality import evaluate_factuality
from evaluation.hallucination import detect_hallucination


DATA_FILE = Path(__file__).parent.parent / "m2_validation.json"


with open(DATA_FILE, "r", encoding="utf-8") as file:
    CASES = json.load(file)


def run_case(case):
    relevance = evaluate_relevance(
        case["question"],
        case["ai_response"],
    )

    accuracy = evaluate_factuality(
        case["question"],
        case["ai_response"],
        case["reference_answer"],
    )

    hallucination = detect_hallucination(
        case["ai_response"],
        case["reference_answer"],
    )

    assert relevance.details["category"] == case["expected_relevance"]
    assert accuracy.details["category"] == case["expected_accuracy"]
    assert (
        hallucination.hallucination_detected
        == case["expected_hallucination"]
    )


def test_qa_01():
    run_case(CASES[0])


def test_qa_02():
    run_case(CASES[1])


def test_qa_03():
    run_case(CASES[2])


def test_qa_04():
    run_case(CASES[3])


def test_qa_05():
    run_case(CASES[4])