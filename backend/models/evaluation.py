from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

from evaluation.common import EvaluationResult
from evaluation.hallucination import HallucinationResult


class EvaluationRequest(BaseModel):
    """Inputs accepted by the evaluation endpoint."""

    question: str = Field(
        ...,
        min_length=1,
        description="The user's question",
    )

    response: str = Field(
        ...,
        min_length=1,
        description="The AI-generated response",
    )

    reference_answer: Optional[str] = Field(
        default=None,
        description="Optional expected answer used for comparison",
    )

    source_document: Optional[str] = Field(
        default=None,
        description="Optional source text used as evaluation context",
    )

    use_knowledge_base: bool = Field(default=False)

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    @field_validator("question", "response")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        """Reject values that contain no meaningful text."""

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "must contain non-whitespace text"
            )

        return cleaned_value

    @property
    def ai_response(self) -> str:
        """Compatibility accessor for the evaluator modules."""

        return self.response


class EvaluationResponse(BaseModel):
    """Structured final report returned by the orchestrator."""

    question: str
    response: str

    retrieved_context: list[str] = Field(
        default_factory=list
    )

    relevance: EvaluationResult
    factuality: EvaluationResult
    faithfulness: EvaluationResult
    completeness: EvaluationResult
    hallucination: HallucinationResult
    semantic_similarity: EvaluationResult

    overall_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=10,
    )

    final_assessment: str

    # Scalar fields remain available for compatibility
    # with the original model.

    relevance_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=10,
    )

    factuality_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=10,
    )

    faithfulness_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=10,
    )

    completeness_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=10,
    )

    semantic_similarity_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=10,
    )

    hallucination_detected: Optional[bool] = None

    hallucination_severity: Optional[
        Literal["LOW", "MEDIUM", "HIGH"]
    ] = None

    explanation: Optional[str] = None

    unsupported_claims: list[str] = Field(
        default_factory=list
    )

    evaluation_reasoning: dict[str, str] = Field(
        default_factory=dict
    )
    