from backend.models.evaluation import EvaluationRequest
from evaluation import orchestrator


def test_orchestrator_evaluates_with_source_context() -> None:
    request = EvaluationRequest(
        question="What is the capital of France?",
        response="Paris is the capital of France.",
        source_document="Paris is the capital of France.",
    )

    result = orchestrator.evaluate_request(request)

    assert result.question == request.question
    assert result.response == request.response
    assert result.faithfulness.score == 10
    assert result.hallucination.hallucination_detected is False
    assert result.semantic_similarity.score is None


def test_orchestrator_uses_mocked_knowledge_base(monkeypatch) -> None:
    monkeypatch.setattr(
        orchestrator,
        "_local_context",
        lambda question, top_k: (["Paris is the capital of France."], None),
    )
    request = EvaluationRequest(
        question="What is the capital of France?",
        response="Paris is the capital of France.",
        use_knowledge_base=True,
        top_k=3,
    )

    result = orchestrator.evaluate_request(request)

    assert result.retrieved_context == ["Paris is the capital of France."]
    assert result.factuality.score == 10


def test_orchestrator_reports_empty_knowledge_base(monkeypatch) -> None:
    monkeypatch.setattr(
        orchestrator,
        "_local_context",
        lambda question, top_k: ([], orchestrator.EMPTY_KNOWLEDGE_BASE_MESSAGE),
    )
    request = EvaluationRequest(
        question="What is the capital of France?",
        response="Paris is the capital of France.",
        use_knowledge_base=True,
    )

    result = orchestrator.evaluate_request(request)

    assert orchestrator.EMPTY_KNOWLEDGE_BASE_MESSAGE in result.final_assessment
    assert result.hallucination.hallucination_detected is None