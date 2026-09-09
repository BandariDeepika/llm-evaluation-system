from typing import Any

from knowledge_base.embeddings import embed_texts
from knowledge_base.vector_store import ChromaVectorStore


def retrieve_context(query: str, store: ChromaVectorStore, top_k: int = 5) -> list[dict[str, Any]]:
    """Embed a query and return the nearest stored chunks."""
    if not query.strip():
        raise ValueError("query must contain text")
    query_embedding = embed_texts([query])[0]
    return store.search(query_embedding, top_k=top_k)