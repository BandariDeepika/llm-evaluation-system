# Automated LLM Evaluation and Hallucination Detection System

## Project Description

This project evaluates AI-generated responses for relevance, factuality, faithfulness, completeness, semantic similarity, and hallucination. It provides individual scores, an overall score, supporting reasoning, retrieved context, unsupported claims, and hallucination severity. A Streamlit web app provides account registration, login/logout, a private dashboard, and per-user evaluation history backed by SQLite.

The project is being completed in stages so that each part can be understood, tested, and explained during an internship evaluation. Stage 6 completes Milestone 1: Streamlit communicates with FastAPI, the orchestrator runs the evaluation engine, and optional local knowledge-base retrieval supplies evidence. The deterministic baseline works without an OpenAI API key.

## Project Objective

The objective is to build a real evaluation system that combines FastAPI, Streamlit, OpenAI LLM-as-a-Judge evaluation, sentence-transformer embeddings, ChromaDB retrieval, and public datasets from Hugging Face.

## Technology Stack

- Python
- FastAPI and Uvicorn
- Streamlit
- OpenAI API
- LangChain and LangGraph
- sentence-transformers with `all-MiniLM-L6-v2`
- ChromaDB
- Hugging Face datasets
- scikit-learn
- pytest

## Planned System Architecture

User -> Streamlit -> FastAPI -> Evaluation Orchestrator -> Knowledge Base / ChromaDB -> Evaluation Agents -> LLM-as-a-Judge -> Scoring Engine -> Evaluation Report -> Streamlit

The knowledge base will be built from TruthfulQA and SQuAD. Optional user source documents will also be processed and searched during evaluation.

## Project Structure

```text
llm-evaluation-system/
├── frontend/
├── backend/
│   ├── api/
│   ├── models/
│   └── services/
├── evaluation/
├── knowledge_base/
├── data/
├── tests/
├── docs/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Current Development Stage

**Web application:** The Streamlit interface is connected to the FastAPI evaluation API and supports individual accounts, evaluation history, dashboard metrics, CSV batch evaluation, and PDF downloads.

Dataset loading, preprocessing, chunking, embedding generation, ChromaDB storage, similarity retrieval, the `/evaluate` endpoint, the orchestrator, and the Streamlit interface are implemented. LLM-as-a-Judge remains a future enhancement.

## Installation

Windows PowerShell commands:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your own OpenAI API key only when the OpenAI integration is implemented. Never commit `.env` to GitHub.

The application creates its SQLite database at `data/aegiseval.db` on first backend startup. Passwords are stored as salted PBKDF2 hashes, not as plain text. To use a different database location, set `APP_DATABASE_PATH` before starting FastAPI.

## Running Instructions

Run these commands from the project root in two PowerShell terminals. Activate the virtual environment in each terminal first:

```powershell
.\.venv\Scripts\Activate.ps1
uvicorn backend.main:app --reload
```

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run frontend/app.py
```

Open the Streamlit URL shown in the terminal, normally `http://localhost:8501`. FastAPI documentation is available at `http://127.0.0.1:8000/docs`.

### Test registration, login, and evaluation

1. Open `http://localhost:8501` and choose **Register**. Enter a full name, valid email, username, and matching password (at least 8 characters).
2. The new account is signed in automatically. Use **Log out**, then sign back in with the username or email and password to verify login.
3. Open **Single Evaluation**, enter a question and an AI response, optionally provide a reference answer or evidence, and select **Evaluate Response**. The existing evaluation agents run through the FastAPI service.
4. Return to **Dashboard** to see your evaluation and verdict counts. Numeric Relevance, Accuracy (the factuality score), Completeness, and Hallucination scores are charted when provided; the current hallucination evaluator also displays its real detected/not-detected/uncertain outcome counts. Metrics without numeric scores are omitted rather than fabricated.
5. Open **History** to see only evaluations saved to your account. **Batch Evaluation** continues to accept CSV uploads and keeps the existing CSV and PDF download options.

Run the tests from the project root:

```powershell
pytest
```

For HTTPS deployments, set `AEGISEVAL_COOKIE_SECURE=true`. The Streamlit client authenticates API requests using its session token; session tokens are stored as hashes in SQLite.

The application does not automatically download datasets during evaluation. Index the local ChromaDB knowledge base separately before enabling retrieval.

## Public deployment (Render API + Streamlit Community Cloud)

The API URL defaults to the project's Render service so the Streamlit Community
Cloud process does not try to reach its own `localhost`. You can override it
with a Streamlit secret named `API_BASE_URL` (or the
`AEGISEVAL_API_URL` environment variable). For local development, set
`AEGISEVAL_API_URL=http://localhost:8000`.

### Render backend

1. In Render, create or update a **Web Service** connected to this repository,
   using the repository root as the root directory.
2. Use `pip install -r requirements.txt` as the build command and
   `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` as the start command.
   Set the health-check path to `/health`.
3. Add a persistent disk mounted at `/var/data` and set
   `APP_DATABASE_PATH=/var/data/aegiseval.db`. The included `render.yaml`
   describes this setup. A persistent disk requires a paid Render instance;
   without it, SQLite accounts, sessions, and history may be lost when the
   service restarts or redeploys.
4. Set `AEGISEVAL_COOKIE_SECURE=true` for the HTTPS deployment. No OpenAI key
   is required by the current deterministic evaluation implementation.

The service uses SQLite, which is appropriate for a single Render instance.
Do not scale this service to multiple instances while using its local SQLite
database. If the existing deployment already has users or history in its
ephemeral `data/aegiseval.db`, changing `APP_DATABASE_PATH` to `/var/data` does
not migrate that file; export or copy the old database before switching paths
if those records must be retained.

### Streamlit Community Cloud frontend

1. Create a Community Cloud app from this repository and set the app file to
   `frontend/app.py`.
2. In **Advanced settings → Secrets**, configure:

   ```toml
   API_BASE_URL = "https://llm-evaluation-system-o5uf.onrender.com"
   API_TIMEOUT_SECONDS = "180"
   ```

   `API_BASE_URL` must be the Render service's public HTTPS URL, without
   `/evaluate` or `/auth`. `API_TIMEOUT_SECONDS` controls the read timeout for
   API calls; the frontend uses a 10-second connection timeout separately.
   The application defaults to 180 seconds because KB-backed evaluations may
   need to load the embedding model on their first use. KB retrieval is
   opt-in; supplying a reference answer or source document avoids that model
   loading path.
3. Redeploy/restart the Streamlit app after changing secrets. Check that
   `https://llm-evaluation-system-o5uf.onrender.com/health` returns HTTP 200,
   then register a test account, log in, run an evaluation, and check History.

Do not commit credentials or local secrets files. Set environment variables
in each hosting provider's dashboard; the public API URL is not a credential.
