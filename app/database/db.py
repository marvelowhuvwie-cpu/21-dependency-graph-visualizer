import json
import sqlite3
from pathlib import Path

from flask import Flask, current_app, g


def get_db():
    """Return the SQLite connection for the current application context."""

    if "db" not in g:
        database_path = Path(current_app.config["DATABASE"])
        database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        connection = sqlite3.connect(
            str(database_path),
            timeout=5.0,
        )
        connection.row_factory = sqlite3.Row

        g.db = connection

    return g.db


def close_db(_error=None):
    """Close the connection when the application context ends."""

    connection = g.pop("db", None)

    if connection is not None:
        connection.close()


def init_db(app: Flask):
    """Create the analysis history table."""

    database_path = Path(app.config["DATABASE"])
    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with app.app_context():
        connection = get_db()

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT NOT NULL,
                node_count INTEGER NOT NULL,
                edge_count INTEGER NOT NULL,
                cycle_count INTEGER NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.commit()

    app.teardown_appcontext(close_db)


def save_analysis(app: Flask, result: dict):
    """Save a completed analysis using parameterized SQL."""

    with app.app_context():
        connection = get_db()
        summary = result["summary"]

        connection.execute(
            """
            INSERT INTO analysis_history (
                project_name,
                node_count,
                edge_count,
                cycle_count,
                result_json
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                summary["projectName"],
                summary["nodeCount"],
                summary["edgeCount"],
                summary["cycleCount"],
                json.dumps(result, separators=(",", ":")),
            ),
        )

        connection.commit()