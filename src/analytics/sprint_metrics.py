from __future__ import annotations
import pandas as pd


def calculate_sprint_metrics(df: pd.DataFrame) -> dict:
    """Calculate transparent sprint metrics for a single sprint dataset."""
    total_points = float(df["story_points"].sum())
    completed_points = float(df.loc[df["status"] == "Done", "story_points"].sum())
    incomplete_points = total_points - completed_points
    blocked_count = int((df["status"] == "Blocked").sum())

    completion = (completed_points / total_points * 100) if total_points else 0.0
    carry_over = (incomplete_points / total_points * 100) if total_points else 0.0

    return {
        "committed_points": total_points,
        "completed_points": completed_points,
        "velocity": completed_points,
        "completion_percentage": round(completion, 1),
        "carry_over_points": incomplete_points,
        "carry_over_percentage": round(carry_over, 1),
        "blocked_stories": blocked_count,
        "total_stories": int(len(df)),
    }
