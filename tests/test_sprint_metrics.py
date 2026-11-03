import pandas as pd
from src.analytics.sprint_metrics import calculate_sprint_metrics


def test_metrics_are_calculated_correctly():
    df = pd.DataFrame({
        "story_points": [8, 5, 3, 4],
        "status": ["Done", "Done", "Blocked", "To Do"],
    })
    result = calculate_sprint_metrics(df)
    assert result["committed_points"] == 20
    assert result["completed_points"] == 13
    assert result["completion_percentage"] == 65.0
    assert result["carry_over_percentage"] == 35.0
    assert result["blocked_stories"] == 1
