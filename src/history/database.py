import sqlite3
from pathlib import Path


# Store the database in the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "agilesense_history.db"


def get_connection():
    """Create a connection to the AgileSense history database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    """Create the sprint history table if it does not exist."""

    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS sprint_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sprint_name TEXT NOT NULL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            committed_points REAL,
            velocity REAL,
            completion_percentage REAL,
            carry_over_percentage REAL,
            blocked_stories INTEGER,
            high_risk_stories INTEGER,
            medium_risk_stories INTEGER,
            unique_stories_at_risk INTEGER,
            health_status TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def save_sprint_history(
    sprint_name,
    metrics,
    high_risk_count,
    medium_risk_count,
    unique_stories_at_risk,
    health_status,
):
    """Save one sprint analysis to historical records."""

    connection = get_connection()

    connection.execute("""
        INSERT INTO sprint_history (
            sprint_name,
            committed_points,
            velocity,
            completion_percentage,
            carry_over_percentage,
            blocked_stories,
            high_risk_stories,
            medium_risk_stories,
            unique_stories_at_risk,
            health_status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        sprint_name,
        metrics["committed_points"],
        metrics["velocity"],
        metrics["completion_percentage"],
        metrics["carry_over_percentage"],
        metrics["blocked_stories"],
        high_risk_count,
        medium_risk_count,
        unique_stories_at_risk,
        health_status,
    ))

    connection.commit()
    connection.close()


def get_sprint_history():
    """Retrieve saved sprint records in chronological order."""

    connection = get_connection()

    records = connection.execute("""
        SELECT *
        FROM sprint_history
        ORDER BY recorded_at ASC, id ASC
    """).fetchall()

    connection.close()

    return [dict(record) for record in records]