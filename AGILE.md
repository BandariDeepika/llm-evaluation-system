# Agile Development Document

## Project Overview

**AegisEval – Automated LLM Evaluation and Hallucination Detection System** is a Python application for evaluating AI-generated responses. Its Streamlit frontend communicates with a FastAPI backend. The backend runs an evaluation orchestrator and can optionally retrieve supporting evidence from a local ChromaDB knowledge base.

The repository separates the application into:

- `frontend/`: Streamlit user interface, API configuration, charts, evaluation workflows, and report presentation.
- `backend/api/`: FastAPI health, authentication, evaluation, and history endpoints.
- `backend/models/`: Request and response schemas for evaluations.
- `backend/database.py`: SQLite persistence for accounts, sessions, and evaluation history.
- `evaluation/`: Evaluation dimensions, scoring, verdict generation, and orchestrator.
- `knowledge_base/`: Data preparation, chunking, embeddings, vector storage, and retrieval.
- `tests/`: Automated tests for API, authentication, evaluation, frontend helpers, and knowledge-base behavior.

## Objectives

1. Provide a usable interface for submitting AI responses for evaluation.
2. Return evidence-based evaluation results, including relevance, factuality, faithfulness, completeness, semantic similarity, and hallucination assessment.
3. Support optional local knowledge-base retrieval when enabled and available.
4. Provide account registration and login, and associate saved evaluation history with authenticated users.
5. Keep the evaluation pipeline, API contracts, and deployment configuration testable and maintainable.

## Agile Methodology

Development follows a lightweight, iterative, milestone-based Agile approach. Work is organized around demonstrable increments, with implementation and tests evolving together. This describes the repository's staged development; it does not imply that formal Scrum ceremonies or a dedicated team were used.

Each increment is expected to:

1. Define a small, observable outcome.
2. Implement the relevant backend, frontend, or evaluation changes.
3. Add or update focused automated tests.
4. Verify behavior locally before considering the increment complete.

## Development Milestones and Sprint Planning

The milestones below summarize the implementation areas represented in the current project. They are not a claim that every possible enhancement is complete.

| Milestone | Scope represented in the repository |
| --- | --- |
| M1 – Evaluation foundation | Evaluation modules, orchestration, API schemas, and the initial evaluation workflow. |
| M2 – Scoring and validation | Evaluation scoring, validation fixtures, and related tests and documentation. |
| M3 – Evaluation quality | Completeness assessment, verdict generation, and hallucination-related evaluation details. |
| Application integration | Streamlit-to-FastAPI workflows, authentication, evaluation history, dashboards, and reports. |
| Deployment readiness | Render configuration, Streamlit API configuration guidance, and environment-based settings. |

For future work, plan short sprints around a testable user outcome. At sprint start, select backlog items and define acceptance checks. During implementation, keep changes scoped and update tests. At sprint end, run the relevant tests, review the user-visible behavior, and record incomplete work for a later sprint.

## Project Backlog and Major Features

### Implemented in the current codebase

- Streamlit interface for authentication, single and batch evaluation workflows, dashboard/results views, and evaluation history.
- FastAPI health, authentication, evaluation, dashboard, and history routes.
- SQLite persistence for user accounts, sessions, and authenticated evaluation records.
- Evaluation orchestration for relevance, factuality, faithfulness, completeness, semantic similarity, hallucination assessment, overall scoring, and a consolidated verdict.
- Optional local evidence retrieval using the knowledge-base and ChromaDB modules.
- API request/response models and pytest coverage across key backend, frontend-helper, evaluation, authentication, and knowledge-base components.
- Render deployment manifest and frontend configuration supporting a deployed API URL and timeout settings.

### Backlog for future iterations

- Review production persistence and operational needs; the current database implementation uses SQLite and its durability depends on deployment storage configuration.
- Improve observability for API failures, evaluation latency, and knowledge-base retrieval without exposing user data or secrets.
- Continue testing deployment-specific behavior, including cold starts, authentication, and evaluation/history workflows.
- Evaluate future LLM-as-a-Judge integration only after defining its requirements, credentials handling, reliability expectations, and validation criteria. It is not described here as an implemented feature.
- Expand evaluation validation with additional datasets, edge cases, and documented acceptance thresholds.

Backlog priority should be based on user impact, correctness, security, deployment risk, and the effort required to deliver a verifiable increment.

## Roles and Responsibilities

This repository does not document a multi-person delivery team. For an individual or small-team project, responsibilities can be assigned as follows:

- **Project maintainer/developer:** Owns implementation, backlog prioritization, code review, documentation, and release preparation.
- **Test/quality responsibility:** Defines acceptance checks, maintains automated tests, and reports regressions. This may be performed by the maintainer in a solo project.
- **Stakeholder or mentor:** Reviews project goals and demonstrations and provides feedback on priorities and expected outcomes.
- **Application user:** Provides feedback on usability and whether evaluation outputs are understandable and useful.

These are responsibility areas, not claims about named contributors or formal appointments.

## Testing and Quality Assurance

The project uses pytest. Tests are organized in `tests/` and cover areas including API behavior, registration and authentication, evaluation endpoints and engine behavior, frontend API/chart helpers, batch workflows, and knowledge-base components. Evaluation-specific validation fixtures and tests are also present in the repository.

For each change:

1. Run focused tests for the modified behavior.
2. Run broader relevant tests when shared interfaces or orchestration change.
3. Check API request and response schemas when endpoint behavior changes.
4. Verify user-visible workflows locally where applicable.
5. Keep secrets out of source control and use deployment environment settings for credentials and service configuration.

Automated tests support quality assurance but do not replace manual verification of hosted services, persistent storage, or deployment settings.

## Progress Tracking

Track work through repository issues or an equivalent prioritized backlog, using clear acceptance criteria and linking implementation and tests to each item. Mark items complete only when the corresponding behavior is implemented and its applicable verification has passed. Record deferred work and known limitations explicitly, especially where behavior depends on external hosting, optional knowledge-base data, or deployment storage.

## Future Improvements

Potential future increments include stronger production observability, expanded evaluation benchmarks, deployment smoke tests, and a reviewed strategy for durable multi-user persistence. Any new evaluation method or external model integration should be added only after its behavior, validation approach, and operational requirements are defined.
