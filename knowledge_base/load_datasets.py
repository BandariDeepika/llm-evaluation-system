from collections.abc import Iterable, Mapping


def load_truthfulqa(split: str = "validation") -> list[dict[str, str]]:
    """Load TruthfulQA and convert each question-answer pair to common records."""
    from datasets import load_dataset

    dataset = load_dataset("truthful_qa", "generation", split=split)
    records: list[dict[str, str]] = []
    for item in dataset:
        answers = item.get("correct_answers", [])
        answer_text = "; ".join(str(answer) for answer in answers)
        records.append({"text": f"Question: {item['question']}\nAnswer: {answer_text}", "source": "TruthfulQA"})
    return records


def load_squad(split: str = "train") -> list[dict[str, str]]:
    """Load SQuAD contexts and questions into common searchable records."""
    from datasets import load_dataset

    dataset = load_dataset("rajpurkar/squad", split=split)
    records: list[dict[str, str]] = []
    for item in dataset:
        records.append({"text": f"Context: {item['context']}\nQuestion: {item['question']}\nAnswer: {item['answers']['text'][0]}", "source": "SQuAD"})
    return records


def load_public_datasets() -> list[dict[str, str]]:
    """Load both configured public datasets and return normalized records."""
    return load_truthfulqa() + load_squad()


def records_from_iterable(records: Iterable[Mapping[str, object]]) -> list[dict[str, str]]:
    """Normalize test or user-provided records without accessing the network."""
    normalized: list[dict[str, str]] = []
    for record in records:
        text = str(record.get("text", "")).strip()
        if text:
            normalized.append({"text": text, "source": str(record.get("source", "custom"))})
    return normalized