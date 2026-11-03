import pandas as pd
from src.risk.risk_engine import identify_delivery_risks


def test_high_priority_blocked_story_creates_high_risk():
    df = pd.DataFrame([{
        "story_id": "US-9", "status": "Blocked", "priority": "High",
        "dependency": "", "blocked_reason": "Waiting on API",
    }])
    metrics = {
        "carry_over_percentage": 0.0,
        "completion_percentage": 100.0,
    }
    risks = identify_delivery_risks(df, metrics)
    assert any(risk["level"] == "High" and risk["story_id"] == "US-9" for risk in risks)


def test_missing_dependencies_do_not_create_dependency_risks():
    df = pd.DataFrame([
        {
            "story_id": "US-146",
            "status": "In Progress",
            "priority": "Medium",
            "dependency": "",
        },
        {
            "story_id": "US-151",
            "status": "To Do",
            "priority": "Medium",
            "dependency": None,
        },
        {
            "story_id": "US-152",
            "status": "In Progress",
            "priority": "Medium",
            "dependency": float("nan"),
        },
    ])

    metrics = {
        "carry_over_percentage": 0.0,
        "completion_percentage": 100.0,
    }

    risks = identify_delivery_risks(df, metrics)

    dependency_risks = [
        risk for risk in risks
        if risk["category"] == "Unresolved dependency"
    ]

    assert len(dependency_risks) == 0


def test_valid_dependency_creates_dependency_risk():
    df = pd.DataFrame([{
        "story_id": "US-143",
        "status": "In Progress",
        "priority": "Medium",
        "dependency": "US-142",
    }])

    metrics = {
        "carry_over_percentage": 0.0,
        "completion_percentage": 100.0,
    }

    risks = identify_delivery_risks(df, metrics)

    assert any(
        risk["category"] == "Unresolved dependency"
        and risk["story_id"] == "US-143"
        and "US-142" in risk["evidence"]
        for risk in risks
    )
