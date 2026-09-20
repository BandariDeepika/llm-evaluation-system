from typing import Optional

from backend.models.evaluation import EvaluationRequest, EvaluationResponse
from evaluation.completeness import evaluate_completeness
from evaluation.factuality import evaluate_factuality
from evaluation.faithfulness import evaluate_faithfulness
from evaluation.hallucination import detect_hallucination
from evaluation.relevance import evaluate_relevance
from evaluation.scoring import calculate_overall_score
from evaluation.semantic_similarity import evaluate_semantic_similarity
from evaluation.verdict import calculate_verdict


EMPTY_KNOWLEDGE_BASE_MESSAGE = (
    "Knowledge base is empty. Please build/index the knowledge base first."
)


def _local_context(
    question: str,
    top_k: int,
) -> tuple[list[str], Optional[str]]:
    """Retrieve local evidence without downloading or indexing datasets."""

    from knowledge_base.retrieval import retrieve_context
    from knowledge_base.vector_store import ChromaVectorStore

    store = ChromaVectorStore()

    if store.collection.count() == 0:
        return [], EMPTY_KNOWLEDGE_BASE_MESSAGE

    matches = retrieve_context(
        question,
        store,
        top_k=top_k,
    )

    context = [
        match["text"]
        for match in matches
    ]

    return context, None


def evaluate_request(
    request: EvaluationRequest,
) -> EvaluationResponse:
    """Run all evaluation agents and assemble the final report."""

    retrieved_context: list[str] = []
    retrieval_note: Optional[str] = None

    evidence = (
        request.source_document.strip()
        if request.source_document
        else None
    )

    # ---------------------------------------------------------
    # Retrieve evidence from Knowledge Base
    # ---------------------------------------------------------

    if request.use_knowledge_base and not evidence:
        try:
            retrieved_context, retrieval_note = _local_context(
                request.question,
                request.top_k,
            )
        except Exception:
            retrieval_note = (
                "Knowledge base retrieval is unavailable. "
                "Evaluation continued without retrieved evidence."
            )

    if retrieved_context:
        evidence = "\n\n".join(retrieved_context)

    # ---------------------------------------------------------
    # Run evaluation agents
    # ---------------------------------------------------------

    relevance = evaluate_relevance(
        request.question,
        request.response,
    )

    factuality = evaluate_factuality(
        request.question,
        request.response,
        request.reference_answer,
        evidence,
    )

    faithfulness = evaluate_faithfulness(
        request.response,
        evidence,
    )

    hallucination = detect_hallucination(
        request.response,
        evidence,
    )

    semantic_similarity = evaluate_semantic_similarity(
        request.response,
        request.reference_answer,
    )

    completeness = evaluate_completeness(
        request.question,
        request.response,
        request.reference_answer,
        evidence,
    )

    # ---------------------------------------------------------
    # Collect evaluation results
    # ---------------------------------------------------------

    results = {
        "relevance": relevance,
        "factuality": factuality,
        "faithfulness": faithfulness,
        "completeness": completeness,
        "semantic_similarity": semantic_similarity,
    }

    # ---------------------------------------------------------
    # Existing M2 overall score
    # Kept for backward compatibility.
    # ---------------------------------------------------------

    overall = calculate_overall_score(results)

    # ---------------------------------------------------------
    # M3.2 Verdict Agent
    # ---------------------------------------------------------

    verdict_result = calculate_verdict(
        relevance=relevance,
        factuality=factuality,
        completeness=completeness,
        hallucination=hallucination,
    )

    # ---------------------------------------------------------
    # Final assessment
    # ---------------------------------------------------------

    notes = [
        verdict_result.consolidated_reasoning
    ]

    if retrieval_note:
        notes.append(retrieval_note)

    if hallucination.certainty == "uncertain":
        notes.append(
            "Hallucination status is uncertain because "
            "no evidence was available."
        )

    final_assessment = " ".join(notes)

    # ---------------------------------------------------------
    # Return structured evaluation response
    # ---------------------------------------------------------

    return EvaluationResponse(
        question=request.question,
        response=request.response,

        retrieved_context=retrieved_context,

        relevance=relevance,
        factuality=factuality,
        faithfulness=faithfulness,
        completeness=completeness,
        hallucination=hallucination,
        semantic_similarity=semantic_similarity,

        # Existing M2 score
        overall_score=overall.score,

        final_assessment=final_assessment,

        relevance_score=relevance.score,
        factuality_score=factuality.score,
        faithfulness_score=faithfulness.score,
        completeness_score=completeness.score,
        semantic_similarity_score=semantic_similarity.score,

        hallucination_detected=(
            hallucination.hallucination_detected
        ),

        hallucination_severity=(
            hallucination.severity
        ),

        explanation=final_assessment,

        unsupported_claims=(
            hallucination.unsupported_claims
        ),

        evaluation_reasoning={
            name: result.explanation
            for name, result in results.items()
        },

        # -----------------------------------------------------
        # M3.1 Completeness details
        # -----------------------------------------------------

        completeness_addressed_aspects=(
            completeness.details.get(
                "addressed_aspects",
                [],
            )
        ),

        completeness_partial_aspects=(
            completeness.details.get(
                "partial_aspects",
                [],
            )
        ),

        completeness_missing_aspects=(
            completeness.details.get(
                "missing_aspects",
                [],
            )
        ),

        completeness_reasoning=(
            completeness.details.get(
                "reasoning",
                completeness.explanation,
            )
        ),

        # -----------------------------------------------------
        # M3.2 Verdict details
        # -----------------------------------------------------

        verdict=verdict_result.verdict,

        verdict_overall_score=(
            verdict_result.overall_score
        ),

        verdict_major_issues=(
            verdict_result.major_issues
        ),

        verdict_consolidated_reasoning=(
            verdict_result.consolidated_reasoning
        ),

        verdict_weights=(
            verdict_result.weights
        ),
    )