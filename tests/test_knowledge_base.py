from knowledge_base.chunking import chunk_text
from knowledge_base.load_datasets import records_from_iterable
from knowledge_base.preprocess import clean_text, preprocess_records


def test_clean_text_normalizes_whitespace() -> None:
    assert clean_text("  Paris\n\t is correct.  ") == "Paris is correct."


def test_records_are_normalized_without_network_access() -> None:
    records = records_from_iterable([{"text": "Answer", "source": "test"}, {"text": ""}])

    assert preprocess_records(records) == [{"text": "Answer", "source": "test"}]


def test_chunk_text_uses_overlap() -> None:
    chunks = chunk_text("one two three four five six", chunk_size=4, overlap=1)

    assert chunks == ["one two three four", "four five six"]