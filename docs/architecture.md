# System Architecture

## Approved Flow

```text
User
  -> Streamlit
  -> FastAPI
  -> Evaluation Orchestrator
  -> Knowledge Base / ChromaDB
  -> Evaluation Agents
  -> LLM-as-a-Judge
  -> Scoring Engine
  -> Evaluation Report
  -> Streamlit
```

## Component Responsibilities

### Streamlit

Streamlit will provide the user interface for entering a question, an AI response, an optional reference answer, and an optional source document. It will display scores, explanations, hallucination status, severity, retrieved context, and unsupported claims.

### FastAPI

FastAPI will expose the application API, validate requests and responses with Pydantic models, and connect the frontend to the evaluation services.

### Evaluation Orchestrator

The orchestrator will coordinate input validation, document processing, retrieval, evaluator execution, scoring, and report generation.

### Knowledge Base and ChromaDB

TruthfulQA and SQuAD content will be cleaned, split into chunks, embedded with `all-MiniLM-L6-v2`, and stored in ChromaDB. Relevant chunks will be retrieved for each evaluation request.

### Evaluation Agents

Separate evaluators will assess relevance, factuality, faithfulness, completeness, semantic similarity, and hallucination. Keeping these responsibilities separate makes the system modular and easier to test.

### LLM-as-a-Judge

The OpenAI API will be used for language-based evaluation and reasoning. The evaluator prompts will request structured results rather than unstructured text.

### Scoring Engine

The scoring engine will validate evaluator output, calculate individual scores, calculate the overall score, and determine hallucination status and severity.

### Evaluation Report

The final report will contain individual scores, overall score, hallucination detection, severity, reasoning, retrieved context, and unsupported claims.

## Knowledge-Base Pipeline

TruthfulQA and SQuAD records are loaded by `knowledge_base/load_datasets.py`, normalized into a common text/source format, cleaned by `preprocess.py`, and split into overlapping word chunks by `chunking.py`. `embeddings.py` uses the `all-MiniLM-L6-v2` sentence-transformer model to create normalized vectors. `vector_store.py` persists those vectors and metadata in ChromaDB. `retrieval.py` embeds a query and returns the nearest chunks with their source metadata and distances.

The public-dataset entry point is `index_public_datasets`. Tests can use `index_records` with in-memory records, avoiding network access and making preprocessing and indexing behavior independently testable.

## Final Milestone 1 Workflow

```text
User Input
  -> Streamlit
  -> FastAPI /evaluate
  -> Evaluation Orchestrator
  -> Optional Knowledge Base Retrieval
  -> Evaluation Modules
  -> Scoring Engine
  -> Final Evaluation Result
```

The orchestrator uses an explicitly supplied source document as evidence first. When no source is supplied and retrieval is enabled, it searches the existing local ChromaDB collection. It does not download or index datasets during an evaluation request.

## Development Boundary

The Stage 6 Milestone 1 integration is implemented. OpenAI LLM-as-a-Judge, authentication, deployment, and advanced analytics remain future enhancements.
