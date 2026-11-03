from pathlib import Path
import sys
from reporting.pdf_report import generate_sprint_report

import pandas as pd
import plotly.express as px
import streamlit as st
from history.database import (
    initialize_database,
    save_sprint_history,
    get_sprint_history,
)
from copilot.ai_copilot import explain_sprint_health

# Initialize sprint history database.
initialize_database()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.csv_validator import validate_csv_bytes
from src.analytics.sprint_metrics import calculate_sprint_metrics
from src.risk.risk_engine import identify_delivery_risks

st.set_page_config(page_title="AgileSense AI", page_icon="📊", layout="wide")

st.title("AgileSense AI")
st.caption("AI Agile Delivery Copilot · MVP preview")
st.info(
    "Portfolio demonstration using synthetic sprint data. "
    "Risk thresholds are illustrative and this version does not yet call an LLM."
)

with st.sidebar:
    st.header("Sprint data")
    uploaded = st.file_uploader("Upload sprint CSV", type=["csv"])
    use_sample = st.button("Load sample sprint data", use_container_width=True)

if "sprint_df" not in st.session_state:
    st.session_state.sprint_df = None

if use_sample:
    sample_path = PROJECT_ROOT / "data" / "sample_sprint_data.csv"
    df, errors, warnings = validate_csv_bytes(sample_path.read_bytes())
    if errors:
        st.error("Sample data validation failed.")
        for error in errors:
            st.write(f"- {error}")
    else:
        st.session_state.sprint_df = df
        st.success("Sample sprint data loaded.")

if uploaded is not None:
    df, errors, warnings = validate_csv_bytes(uploaded.getvalue())
    if errors:
        st.error("Please correct the uploaded file:")
        for error in errors:
            st.write(f"- {error}")
    else:
        st.session_state.sprint_df = df
        st.success("CSV validated and loaded.")
        for warning in warnings:
            st.warning(warning)

df = st.session_state.sprint_df

if df is None:
    st.subheader("Get started")
    st.write("Upload a sprint CSV or choose **Load sample sprint data** in the sidebar.")
    st.markdown("The sample dataset includes completed, in-progress, blocked, and dependent stories.")
    st.stop()

sprint_names = df[["sprint_id", "sprint_name"]].drop_duplicates()
selected = st.selectbox(
    "Select sprint",
    sprint_names["sprint_id"].tolist(),
    format_func=lambda value: sprint_names.loc[sprint_names["sprint_id"] == value, "sprint_name"].iloc[0],
)
sprint_df = df[df["sprint_id"] == selected].copy()
metrics = calculate_sprint_metrics(sprint_df)
risks = identify_delivery_risks(sprint_df, metrics)


# Consolidate story-level risks for the stakeholder summary.
story_risk_levels = {}

for risk in risks:
    story_id = risk["story_id"]

    # Sprint-level risks do not belong to an individual story.
    if story_id is None:
        continue

    current_level = story_risk_levels.get(story_id)

    # High takes precedence over Medium for the same story.
    if current_level is None or risk["level"] == "High":
        story_risk_levels[story_id] = risk["level"]

high_risk_count = sum(
    1 for level in story_risk_levels.values()
    if level == "High"
)

medium_risk_count = sum(
    1 for level in story_risk_levels.values()
    if level == "Medium"
)

unique_stories_at_risk = len(story_risk_levels)

sprint_level_risks = [
    risk for risk in risks
    if risk["story_id"] is None
]


# Build a stakeholder-ready sprint health assessment.

if high_risk_count > 0 or sprint_level_risks:
    health_status = "AT RISK"
    health_message = (
        f"{sprint_df['sprint_name'].iloc[0]} requires attention. "
        f"It has {high_risk_count} high-risk stories and "
        f"{len(sprint_level_risks)} sprint-level risk indicators."
    )
elif medium_risk_count > 0:
    health_status = "NEEDS ATTENTION"
    health_message = (
        f"{sprint_df['sprint_name'].iloc[0]} has medium-risk stories "
        "that should be monitored."
    )
else:
    health_status = "ON TRACK"
    health_message = (
        f"{sprint_df['sprint_name'].iloc[0]} has no risks identified "
        "by the current assessment rules."
    )

# Identify the main reasons for the assessment.
risk_driver_counts = {}

for risk in risks:
    category = risk["category"]
    risk_driver_counts[category] = (
        risk_driver_counts.get(category, 0) + 1
    )

primary_drivers = []

if metrics["completion_percentage"] < 70:
    primary_drivers.append(
        f"Sprint completion is {metrics['completion_percentage']}%, "
        "below the 70% threshold."
    )

if metrics["carry_over_percentage"] > 25:
    primary_drivers.append(
        f"Carry-over is {metrics['carry_over_percentage']}%, "
        "above the 25% threshold."
    )

if risk_driver_counts.get("Blocked story", 0) > 0:
    primary_drivers.append(
        f"{risk_driver_counts['Blocked story']} blocked-story risk alerts "
        "require investigation."
    )

if risk_driver_counts.get("Unresolved dependency", 0) > 0:
    primary_drivers.append(
        f"{risk_driver_counts['Unresolved dependency']} unresolved dependency "
        "alerts require attention."
    )

# Prioritise and de-duplicate recommended actions.
recommended_actions = []

for risk in risks:
    if risk["level"] == "High":
        action = risk["recommendation"]
        if action not in recommended_actions:
            recommended_actions.append(action)

for risk in sprint_level_risks:
    action = risk["recommendation"]
    if action not in recommended_actions:
        recommended_actions.append(action)

recommended_actions = recommended_actions[:5]


st.subheader("Sprint Risk Summary")

r1, r2, r3, r4 = st.columns(4)

r1.metric("Unique stories at risk", unique_stories_at_risk)
r2.metric("High-risk stories", high_risk_count)
r3.metric("Medium-risk stories", medium_risk_count)
r4.metric("Sprint-level risks", len(sprint_level_risks))

if high_risk_count > 0:
    st.error(
        f"{high_risk_count} unique stories have at least one High-risk alert. "
        "Review these stories with their owners."
    )
elif medium_risk_count > 0:
    st.warning("Medium-risk stories need attention.")
else:
    st.success("No story-level risks identified.")

if sprint_level_risks:
    with st.expander("View sprint-level risks"):
        for risk in sprint_level_risks:
            st.write(f"**{risk['level']} · {risk['category']}**")
            st.write(f"Evidence: {risk['evidence']}")
            st.write(f"Suggested action: {risk['recommendation']}")


# Stakeholder-ready sprint health assessment.
st.subheader("Stakeholder Sprint Health Assessment")

if health_status == "AT RISK":
    st.error(f"Overall Health: {health_status}")
elif health_status == "NEEDS ATTENTION":
    st.warning(f"Overall Health: {health_status}")
else:
    st.success(f"Overall Health: {health_status}")

st.write(health_message)

health_left, health_right = st.columns(2)

with health_left:
    st.markdown("#### Primary risk drivers")

    if primary_drivers:
        for driver in primary_drivers:
            st.markdown(f"- {driver}")
    else:
        st.write("No significant risk drivers identified.")

with health_right:
    st.markdown("#### Recommended management actions")

    if recommended_actions:
        for index, action in enumerate(recommended_actions, start=1):
            st.markdown(f"{index}. {action}")
    else:
        st.write("Continue monitoring sprint progress.")

st.caption(
    "Assessment is based on configured thresholds and rule-based risk "
    "indicators. It is decision support, not a prediction of sprint failure."
)

st.divider()

st.subheader("🤖 AI Sprint Copilot")

st.write(
    "Generate an AI-powered explanation of sprint health "
    "and practical recommendations for your team."
)

if st.button("Generate AI Sprint Analysis"):
    try:
        with st.spinner("AgileSense AI is analysing your sprint..."):

            ai_explanation = explain_sprint_health(
                sprint_name=sprint_df["sprint_name"].iloc[0],
                health_status=health_status,
                health_message=health_message,
                metrics=metrics,
                primary_drivers=primary_drivers,
                recommended_actions=recommended_actions,
            )

        st.markdown("### AI Sprint Health Explanation")
        st.markdown(ai_explanation)

    except Exception as error:
        st.error(f"Unable to generate AI analysis: {error}")


st.divider()
# Save the current sprint analysis to historical records.
st.subheader("Sprint History")

if st.button("Save Sprint to History"):
    try:
        save_sprint_history(
            sprint_name=sprint_df["sprint_name"].iloc[0],
            metrics=metrics,
            high_risk_count=high_risk_count,
            medium_risk_count=medium_risk_count,
            unique_stories_at_risk=unique_stories_at_risk,
            health_status=health_status,
        )

        st.success(
            f"{sprint_df['sprint_name'].iloc[0]} saved successfully "
            "to sprint history!"
        )

    except Exception as error:
        st.error(f"Unable to save sprint history: {error}")

# Display previously saved sprint records.
st.markdown("### Saved Sprint Records")

history_records = get_sprint_history()

if history_records:
    st.dataframe(
        history_records,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        f"Total historical sprint records: {len(history_records)}"
    )
        # Sprint Velocity Trend
    st.markdown("### Sprint Velocity Trend")

    velocity_chart = px.line(
        history_records,
        x="recorded_at",
        y="velocity",
        markers=True,
        hover_data=["sprint_name"],
        title="Completed Story Points Across Saved Sprint Records",
    )

    velocity_chart.update_layout(
        xaxis_title="Date Recorded",
        yaxis_title="Velocity (Story Points)",
    )

    st.plotly_chart(
        velocity_chart,
        use_container_width=True,
    )

    st.caption(
        "Velocity represents the completed story points recorded "
        "for each saved sprint analysis."
    )
else:
    st.info("No sprint history available yet. Save a sprint to get started.")
# Generate downloadable stakeholder PDF report.
pdf_report = generate_sprint_report(
    sprint_df=sprint_df,
    metrics=metrics,
    health_status=health_status,
    health_message=health_message,
    high_risk_count=high_risk_count,
    medium_risk_count=medium_risk_count,
    unique_stories_at_risk=unique_stories_at_risk,
    sprint_level_risks=sprint_level_risks,
    risks=risks,
    primary_drivers=primary_drivers,
    recommended_actions=recommended_actions,
)

st.download_button(
    label="Download Sprint Stakeholder Report (PDF)",
    data=pdf_report,
    file_name=f"{sprint_df['sprint_name'].iloc[0]}_Stakeholder_Report.pdf",
    mime="application/pdf",
)

st.subheader(f"Delivery overview · {sprint_df['sprint_name'].iloc[0]}")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Completion", f"{metrics['completion_percentage']}%")
c2.metric("Velocity", f"{metrics['velocity']:g} SP")
c3.metric("Committed", f"{metrics['committed_points']:g} SP")
c4.metric("Blocked stories", metrics["blocked_stories"])
c5.metric("Carry-over", f"{metrics['carry_over_percentage']}%")

left, right = st.columns([1.15, 1])
with left:
    st.markdown("#### Story status")
    status_counts = sprint_df["status"].value_counts().rename_axis("Status").reset_index(name="Stories")
    fig = px.bar(status_counts, x="Status", y="Stories", text="Stories")
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.markdown("#### Delivery risks")
    if not risks:
        st.success("No risks identified by the current rules.")
    else:
        for risk in risks:
            label = f"{risk['level']} · {risk['category']}"
            with st.expander(label, expanded=risk["level"] == "High"):
                if risk["story_id"]:
                    st.write(f"**Story:** {risk['story_id']}")
                st.write(f"**Evidence:** {risk['evidence']}")
                st.write(f"**Suggested action:** {risk['recommendation']}")

st.markdown("#### Sprint backlog")
display_cols = [
    "story_id", "story_title", "story_points", "status",
    "priority", "assignee", "dependency", "blocked_reason",
]
st.dataframe(sprint_df[display_cols], use_container_width=True, hide_index=True)

st.caption(
    "Metrics describe the uploaded dataset and its stated scope. "
    "Risk findings are rule-based indicators, not predictions of sprint failure."
)
