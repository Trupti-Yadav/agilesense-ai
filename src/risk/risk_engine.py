from __future__ import annotations
import pandas as pd


def clean_optional_text(value) -> str:
    """Convert missing or blank values into an empty string."""
    if pd.isna(value):
        return ""

    text = str(value).strip()

    if text.casefold() in {"nan", "none", "null"}:
        return ""

    return text


def identify_delivery_risks(
    df: pd.DataFrame,
    metrics: dict,
    carry_over_threshold: float = 25.0,
    completion_threshold: float = 70.0,
) -> list[dict]:
    """Return explainable rule-based risks; thresholds are illustrative."""
    risks: list[dict] = []

    for _, row in df.iterrows():
        status = clean_optional_text(row["status"])
        priority = clean_optional_text(row.get("priority", "Medium")) or "Medium"
        story_id = str(row["story_id"])

        if status == "Blocked":
            level = "High" if priority == "High" else "Medium"
            blocked_reason = (
                clean_optional_text(row.get("blocked_reason"))
                or "Not supplied"
            )

            risks.append({
                "category": "Blocked story",
                "level": level,
                "story_id": story_id,
                "evidence": (
                    f"{story_id} is blocked. Reason: {blocked_reason}."
                ),
                "recommendation": (
                    "Review the blocker with its owner and agree an unblock action."
                ),
            })

        # Clean the dependency before evaluating the risk.
        dependency = clean_optional_text(row.get("dependency"))

        if dependency and status != "Done":
            risks.append({
                "category": "Unresolved dependency",
                "level": "High",
                "story_id": story_id,
                "evidence": (
                    f"{story_id} is not Done and lists dependency: {dependency}."
                ),
                "recommendation": (
                    "Confirm dependency ownership, expected resolution date, "
                    "and sprint impact."
                ),
            })

    if metrics["carry_over_percentage"] > carry_over_threshold:
        risks.append({
            "category": "High carry-over",
            "level": "Medium",
            "story_id": None,
            "evidence": (
                f"{metrics['carry_over_percentage']}% of committed story points "
                f"are incomplete; configured threshold is {carry_over_threshold}%."
            ),
            "recommendation": (
                "Review remaining scope and identify work that should be re-planned."
            ),
        })

    if metrics["completion_percentage"] < completion_threshold:
        risks.append({
            "category": "Low sprint completion",
            "level": "Medium",
            "story_id": None,
            "evidence": (
                f"Completion is {metrics['completion_percentage']}%; "
                f"configured threshold is {completion_threshold}%."
            ),
            "recommendation": (
                "Review remaining work, blockers, and scope changes with the team."
            ),
        })

    return risks
