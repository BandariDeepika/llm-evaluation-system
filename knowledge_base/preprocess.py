import re


def clean_text(text: str) -> str:
    """Normalize whitespace and remove control characters from source text."""
    cleaned = re.sub(r"[\x00-\x1f\x7f]", " ", text)
    return re.sub(r"\s+", " ", cleaned).strip()


def preprocess_records(records: list[dict[str, str]]) -> list[dict[str, str]]:
    """Clean record text while retaining its source label."""
    processed: list[dict[str, str]] = []
    for record in records:
        text = clean_text(record.get("text", ""))
        if text:
            processed.append({"text": text, "source": record.get("source", "unknown")})
    return processed