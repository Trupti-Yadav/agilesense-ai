# AgileSense AI — System Architecture

## MVP architecture

AgileSense AI is implemented as a modular Python application:
- Streamlit presentation layer
- CSV ingestion and validation module
- Deterministic sprint analytics module
- Explainable rule-based risk engine
- SQLite persistence and LLM integration are planned follow-on capabilities

## Key design decisions

1. Start with a modular monolith rather than microservices.
2. Calculate metrics in deterministic Python code.
3. Use transparent rules for the initial risk engine.
4. Keep AI explanations separate from metric calculations.
5. Keep sample data synthetic and avoid uploading confidential work data.

## Current data flow

CSV upload → validation → sprint metrics → risk rules → dashboard.

## Planned AI flow

User question → context builder → selected sprint metrics and risks → LLM → response checks → answer with evidence.

The LLM integration is not part of the current starter implementation.
