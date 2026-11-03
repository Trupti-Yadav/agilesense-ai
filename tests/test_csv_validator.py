import pandas as pd
from src.ingestion.csv_validator import validate_sprint_dataframe


def valid_data():
    return pd.DataFrame([{
        "sprint_id": "S1", "sprint_name": "Sprint 1",
        "start_date": "2026-01-01", "end_date": "2026-01-14",
        "story_id": "US-1", "story_title": "Example",
        "story_points": 3, "status": "Done",
    }])


def test_valid_dataframe_passes():
    clean, errors, warnings = validate_sprint_dataframe(valid_data())
    assert clean is not None
    assert errors == []


def test_missing_required_column_fails():
    df = valid_data().drop(columns=["story_id"])
    clean, errors, _ = validate_sprint_dataframe(df)
    assert clean is None
    assert "story_id" in errors[0]


def test_invalid_status_fails():
    df = valid_data()
    df.loc[0, "status"] = "Doing"
    clean, errors, _ = validate_sprint_dataframe(df)
    assert clean is None
    assert any("Invalid status" in error for error in errors)
