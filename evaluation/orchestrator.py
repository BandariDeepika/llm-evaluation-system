from pathlib import Path
from typing import Optional

from backend.models.evaluation import EvaluationRequest, EvaluationResponse
from evaluation.completeness import evaluate_completeness
from evaluation.factuality import evaluate_factuality
from evaluation.faithfulness import evaluate_faithfulness
from evaluation.hallucination import detect_hallucination
from evaluation.relevance import evaluate_relevance
from evaluation.scoring import calculate_overall_score
from evaluation.semantic_similarity import evaluate_semantic_similarity


EMPTY_KNOWLEDGE_BASE_MESSAGE = "Knowledge base is empty. Please build/index the knowledge base first."


def _local_context(question: str, top_k: int) -> tuple[list[str], Optional[str]]:
    """Retrieve local evidence without downloading or indexing datasets."""
    from knowledge_base.retrieval import retrieve_context
    from knowledge_base.vector_store import ChromaVectorStore

    store = ChromaVectorStore()
    if store.collection.count() == 0:
        return [], EMPTY_KNOWLEDGE_BASE_MESSAGE
    matches = retrieve_context(question, store, top_k=top_k)
    context = [match["text"] for match in matches]
    return context, None


def evaluate_request(request: EvaluationRequest) -> EvaluationResponse:
    """Run all available evaluators and assemble one final report."""
    retrieved_context: list[str] = []
    retrieval_note: Optional[str] = None
    evidence = request.source_document.strip() if request.source_document else None

    if request.use_knowledge_base and not evidence:
        try:
            retrieved_context, retrieval_note = _local_context(request.question, request.top_k)
        except Exception:
            retrieval_note = "Knowledge base retrieval is unavailable. Evaluation continued without retrieved evidence."

    if retrieved_context:
        evidence = "\n\n".join(retrieved_context)
    factuality = evaluate_factuality(request.question, request.response, request.reference_answer, evidence)
    faithfulness = evaluate_faithfulness(request.response, evidence)
    hallucination = detect_hallucination(request.response, evidence)
    semantic_similarity = evaluate_semantic_similarity(request.response, request.reference_answer)
    results = {
        "relevance": evaluate_relevance(request.question, request.response),
        "factuality": factuality,
        "faithfulness": faithfulness,
        "completeness": evaluate_completeness(request.question, request.response, request.reference_answer),
        "semantic_similarity": semantic_similarity,
    }
    overall = calculate_overall_score(results)
    notes = [overall.explanation]
    if retrieval_note:
        notes.append(retrieval_note)
    if hallucination.certainty == "uncertain":
        notes.append("Hallucination status is uncertain because no evidence was available.")
    final_assessment = " ".join(notes)
    return EvaluationResponse(
        question=request.question,
        response=request.response,
        retrieved_context=retrieved_context,
        relevance=results["relevance"],
        factuality=factuality,
        faithfulness=faithfulness,
        completeness=results["completeness"],
        hallucination=hallucination,
        semantic_similarity=semantic_similarity,
        overall_score=overall.score,
        final_assessment=final_assessment,
        relevance_score=results["relevance"].score,
        factuality_score=factuality.score,
        faithfulness_score=faithfulness.score,
        completeness_score=results["completeness"].score,
        semantic_similarity_score=semantic_similarity.score,
        explanation=final_assessment,
        hallucination_detected=hallucination.hallucination_detected,
        hallucination_severity=hallucination.severity,
        unsupported_claims=hallucination.unsupported_claims,
        evaluation_reasoning={name: result.explanation for name, result in results.items()},
    )