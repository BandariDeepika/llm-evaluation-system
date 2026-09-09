# Evaluation Methodology

This document defines the evaluation dimensions and the Stage 4 baseline engine. The current non-embedding evaluators are deterministic heuristics, not LLM judgments.

## Relevance

Measures whether the AI response directly addresses the user question. A response that is focused and answers the requested topic should score highly. An unrelated or evasive response should score low.

## Factuality

Measures whether factual claims in the response are correct. The evaluator will compare claims with available reference answers, retrieved context, source documents, and other appropriate evidence.

## Faithfulness / Groundedness

Measures whether the response is supported by the supplied or retrieved context. Claims that cannot be supported by the available evidence reduce this score.

## Completeness

Measures whether the response covers the important parts of the question. Multi-part questions will require each meaningful part to be addressed.

## Semantic Similarity

Measures meaning-level similarity between the AI response and an optional reference answer. Sentence-transformer embeddings will be used for this comparison. This dimension is applicable only when a reference answer is supplied.

## Hallucination Detection

Identifies unsupported, fabricated, or contradictory claims. The result will include whether hallucination was detected, the severity (`LOW`, `MEDIUM`, or `HIGH`), unsupported claims, and reasoning.

## Overall Scoring

Scores use a 0-10 scale. The initial weighted formula is:

```text
overall = (relevance * 0.20 + factuality * 0.25 + faithfulness * 0.25
		   + completeness * 0.15 + semantic_similarity * 0.15)
		   / sum(weights for available dimensions)
```

Unavailable dimensions are removed from both the numerator and denominator. Therefore, missing semantic similarity does not silently become zero.

## Inputs and Limitations

Relevance requires a question and response. Factuality requires a response plus reference information or context. Faithfulness requires a response and context. Completeness requires a question and response, with an optional reference answer. Semantic similarity requires both texts and uses `all-MiniLM-L6-v2` embeddings with cosine similarity. Hallucination detection requires evidence to make a certain determination; without evidence it returns an uncertain result.

The token-overlap baseline can miss paraphrases, negation, and subtle contradictions. It is useful for a transparent first implementation but does not replace expert review or an LLM-as-a-Judge. A future integration can provide an LLM judge through the same structured result pattern without changing the scoring contract.

## Integrated Evaluation

The Stage 6 orchestrator accepts a question, response, optional reference answer, optional source document, and optional local knowledge-base retrieval. It runs every applicable evaluator and returns structured results through FastAPI. The Streamlit client displays the report. OpenAI is not required for this baseline; LLM-as-a-Judge remains a future enhancement.
