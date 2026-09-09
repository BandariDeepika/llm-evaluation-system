from pathlib import Path
from typing import Any


class ChromaVectorStore:
    """Small ChromaDB adapter for storing and querying embedded chunks."""

    def __init__(self, persist_directory: str = "data/chroma", collection_name: str = "knowledge_base") -> None:
        import chromadb

        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add_documents(self, texts: list[str], embeddings: list[list[float]], metadatas: list[dict[str, Any]], ids: list[str]) -> None:
        if not (len(texts) == len(embeddings) == len(metadatas) == len(ids)):
            raise ValueError("texts, embeddings, metadatas, and ids must have equal lengths")
        if texts:
            self.collection.upsert(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        result = self.collection.query(query_embeddings=[query_embedding], n_results=top_k)
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            {"text": text, "metadata": metadata or {}, "distance": distance}
            for text, metadata, distance in zip(documents, metadatas, distances)
        ]