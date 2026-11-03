from __future__ import annotations

from io import BytesIO
import pandas as pd

REQUIRED_COLUMNS = {
    "sprint_id", "sprint_name", "start_date", "end_date",
    "story_id", "story_title", "story_points", "status",
}
OPTIONAL_COLUMNS = {
    "priority", "assignee", "dependency", "blocked_reason",
}
VALID_STATUSES = {"To Do", "In Progress", "Done", "Blocked"}
VALID_PRIORITIES = {"High", "Medium", "Low"}


def validate_sprint_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame | None, list[str], list[str]]:
    """Validate sprint rows. Returns (clean_df, errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    missing = sorted(REQUIRED_COLUMNS - set(df.columns))
    if missing:
        return None, [f"Missing required columns: {', '.join(missing)}"], warnings

    clean = df.copy()
    for col in REQUIRED_COLUMNS:
        if clean[col].isna().any():
            rows = (clean.index[clean[col].isna()] + 2).tolist()
            errors.append(f"Column '{col}' has blank values in CSV row(s): {rows}")

    clean["story_points"] = pd.to_numeric(clean["story_points"], errors="coerce")
    bad_points = clean["story_points"].isna() | (clean["story_points"] < 0)
    if bad_points.any():
        rows = (clean.index[bad_points] + 2).tolist()
        errors.append(f"Story points must be non-negative numbers. Check CSV row(s): {rows}")

    clean["status"] = clean["status"].astype("string").str.strip()
    bad_status = ~clean["status"].isin(VALID_STATUSES)
    if bad_status.any():
        values = sorted(clean.loc[bad_status, "status"].dropna().astype(str).unique())
        errors.append(f"Invalid status value(s): {', '.join(values)}. Allowed: {', '.join(sorted(VALID_STATUSES))}")

    if "priority" in clean.columns:
        clean["priority"] = clean["priority"].fillna("Medium").astype("string").str.strip()
        bad_priority = ~clean["priority"].isin(VALID_PRIORITIES)
        if bad_priority.any():
            values = sorted(clean.loc[bad_priority, "priority"].dropna().astype(str).unique())
            errors.append(f"Invalid priority value(s): {', '.join(values)}. Allowed: {', '.join(sorted(VALID_PRIORITIES))}")
    else:
        clean["priority"] = "Medium"
        warnings.append("Priority column not provided; defaulted to Medium.")

    for col in OPTIONAL_COLUMNS:
        if col not in clean.columns:
            clean[col] = ""

    duplicate = clean["story_id"].duplicated(keep=False)
    if duplicate.any():
        ids = sorted(clean.loc[duplicate, "story_id"].astype(str).unique())
        errors.append(f"Duplicate story ID(s): {', '.join(ids)}")

    for col in ("start_date", "end_date"):
        clean[col] = pd.to_datetime(clean[col], errors="coerce")
        if clean[col].isna().any():
            rows = (clean.index[clean[col].isna()] + 2).tolist()
            errors.append(f"Invalid or missing {col} in CSV row(s): {rows}")

    if not errors and (clean["start_date"] >= clean["end_date"]).any():
        errors.append("Each sprint start_date must be earlier than end_date.")

    if errors:
        return None, errors, warnings

    return clean.reset_index(drop=True), errors, warnings


def validate_csv_bytes(contents: bytes) -> tuple[pd.DataFrame | None, list[str], list[str]]:
    try:
        df = pd.read_csv(BytesIO(contents))
    except Exception as exc:
        return None, [f"Could not read CSV file: {exc}"], []
    if df.empty:
        return None, ["The uploaded CSV contains no data rows."], []
    return validate_sprint_dataframe(df)
