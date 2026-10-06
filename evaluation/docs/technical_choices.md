# Technical Choices

## Python

Python has a large ecosystem for machine learning, natural language processing, APIs, testing, and data processing. It is also beginner-friendly and well suited to the project requirements.

## Streamlit

Streamlit provides a simple way to create an interactive evaluation interface in Python without requiring a separate frontend framework.

## FastAPI

FastAPI provides a modern, typed, and high-performance backend API. It automatically documents endpoints and works well with Pydantic validation.

## OpenAI API

The OpenAI API will provide the LLM-as-a-Judge capability for evaluating language-based qualities and generating explanations. The API key will be loaded from an environment file and never placed in source code.

## LangChain

LangChain provides reusable components for prompts, model calls, document handling, and retrieval workflows.

## LangGraph

LangGraph can represent the evaluation workflow as a sequence or graph of coordinated steps. It is useful when evaluation agents need explicit orchestration and state passing.

## sentence-transformers

Sentence-transformers provide local text embeddings. The `all-MiniLM-L6-v2` model is lightweight and suitable for semantic similarity and retrieval experiments.

## ChromaDB

ChromaDB is a practical vector database for storing embeddings and searching for semantically relevant document chunks during evaluation.

## Hugging Face datasets

The datasets library provides a standard way to download and process public datasets such as TruthfulQA and SQuAD for the knowledge base.

## Design Principle

The technologies are selected to keep the project modular, explainable, and suitable for incremental development. Each component can be tested independently before integration.

## Milestone 1 Integration

FastAPI and Streamlit communicate over HTTP. The evaluation orchestrator is the single coordination point between request validation, optional ChromaDB retrieval, evaluation modules, and scoring. The baseline remains usable without an OpenAI API key, keeping local testing deterministic.
