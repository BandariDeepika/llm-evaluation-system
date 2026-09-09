from functools import lru_cache


@lru_cache(maxsize=1)
def get_embedding_model():
    """Load the embedding model only when indexing or retrieval needs it."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("all-MiniLM-L6-v2")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Generate normalized embeddings for a list of texts."""
    if not texts:
        return []
    embeddings = get_embedding_model().encode(texts, normalize_embeddings=True)
    return embeddings.tolist()