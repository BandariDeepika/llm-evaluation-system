
import pandas as pd
from pathlib import Path


BATCH_CSV = Path("frontend/m3_batch_test.csv")


def test_batch_csv_exists():
    """Verify that the batch evaluation CSV exists."""
    assert BATCH_CSV.exists(), "Batch evaluation CSV not found"


def test_batch_csv_has_required_columns():
    """Verify that the batch CSV has the required input columns."""
    df = pd.read_csv(BATCH_CSV)

    assert not df.empty
    assert "question" in df.columns
    assert "ai_response" in df.columns
    assert "reference_answer" in df.columns


def test_batch_csv_contains_multiple_records():
    """Verify that the batch CSV contains multiple evaluation records."""
    df = pd.read_csv(BATCH_CSV)

    assert len(df) >= 2


def test_batch_csv_records_are_not_empty():
    """Verify that question, AI response, and reference answer values are present."""
    df = pd.read_csv(BATCH_CSV)

    assert df["question"].notna().all()
    assert df["ai_response"].notna().all()
    assert df["reference_answer"].notna().all()
