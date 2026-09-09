# Automated LLM Evaluation and Hallucination Detection System

## Project Description

This project will evaluate AI-generated responses for relevance, factuality, faithfulness, completeness, semantic similarity, and hallucination. It will provide individual scores, an overall score, supporting reasoning, retrieved context, unsupported claims, and hallucination severity.

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

**Stage 6: Final Milestone 1 integration.**

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

## Running Instructions

Run these commands from the project root in two terminals:

```powershell
uvicorn backend.main:app --reload
```

```powershell
streamlit run frontend/app.py
```

Open the Streamlit URL shown in the terminal, normally `http://localhost:8501`. FastAPI documentation is available at `http://127.0.0.1:8000/docs`.

The application does not automatically download datasets during evaluation. Index the local ChromaDB knowledge base separately before enabling retrieval.
