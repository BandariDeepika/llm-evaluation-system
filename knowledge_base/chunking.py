def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into word-based chunks with bounded overlap."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")
    words = text.split()
    chunks: list[str] = []
    step = chunk_size - overlap
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + chunk_size])
        if chunk:
            chunks.append(chunk)
        if start + chunk_size >= len(words):
            break
    return chunks


def chunk_records(records: list[dict[str, str]], chunk_size: int = 500, overlap: int = 50) -> list[dict[str, str]]:
    """Chunk records and preserve their source metadata."""
    chunks: list[dict[str, str]] = []
    for record in records:
        for text in chunk_text(record["text"], chunk_size, overlap):
            chunks.append({"text": text, "source": record.get("source", "unknown")})
    return chunks