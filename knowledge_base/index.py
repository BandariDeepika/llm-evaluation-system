from knowledge_base.chunking import chunk_records
from knowledge_base.embeddings import embed_texts
from knowledge_base.load_datasets import load_public_datasets
from knowledge_base.preprocess import preprocess_records
from knowledge_base.vector_store import ChromaVectorStore


def index_records(records: list[dict[str, str]], store: ChromaVectorStore, chunk_size: int = 500, overlap: int = 50) -> int:
    """Preprocess, chunk, embed, and store normalized records."""
    chunks = chunk_records(preprocess_records(records), chunk_size, overlap)
    texts = [chunk["text"] for chunk in chunks]
    embeddings = embed_texts(texts)
    store.add_documents(
        texts=texts,
        embeddings=embeddings,
        metadatas=[{"source": chunk["source"]} for chunk in chunks],
        ids=[f"chunk-{index}" for index in range(len(chunks))],
    )
    return len(chunks)


def index_public_datasets(store: ChromaVectorStore, chunk_size: int = 500, overlap: int = 50) -> int:
    """Download the configured datasets and index them into ChromaDB."""
    return index_records(load_public_datasets(), store, chunk_size, overlap)