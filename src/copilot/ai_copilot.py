
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()


def explain_sprint_health(
    sprint_name,
    health_status,
    health_message,
    metrics,
    primary_drivers,
    recommended_actions,
):
    """
    Generate an AI explanation of sprint health
    using existing AgileSense AI analysis.
    """

    sprint_context = f"""
    Sprint Name: {sprint_name}
    Sprint Health: {health_status}
    Health Assessment: {health_message}

    Sprint Metrics:
    - Committed Points: {metrics['committed_points']}
    - Completed Points (Velocity): {metrics['velocity']}
    - Completion Percentage: {metrics['completion_percentage']}%
    - Carry-over Percentage: {metrics['carry_over_percentage']}%
    - Blocked Stories: {metrics['blocked_stories']}

    Primary Risk Drivers:
    {primary_drivers}

    Recommended Actions:
    {recommended_actions}
    """

    instructions = """
    You are AgileSense AI, an experienced Agile delivery advisor.

    Explain sprint health in clear, professional language for
    Scrum Masters, Product Owners and stakeholders.

    Structure your response using these sections:
    1. Sprint Health Overview
    2. Key Delivery Concerns
    3. Recommended Scrum Master Actions
    4. Stakeholder Communication

    Important rules:
    - Use only the supplied sprint information.
    - Do not invent metrics or risk findings.
    - Do not change the supplied health status.
    - Clearly distinguish facts from recommendations.
    - Be practical, concise and constructive.
    """

    response = client.responses.create(
        model="gpt-5.5",
        instructions=instructions,
        input=sprint_context,
    )

    return response.output_text
