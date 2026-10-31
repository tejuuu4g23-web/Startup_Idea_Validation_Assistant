"""SQLite persistence for startup idea evaluations."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "database" / "startup_validation.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS evaluations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idea_name TEXT NOT NULL,
    industry TEXT NOT NULL,
    description TEXT NOT NULL,
    problem TEXT NOT NULL,
    solution TEXT NOT NULL,
    target_customers TEXT NOT NULL,
    geographic_market TEXT NOT NULL,
    uvp TEXT NOT NULL,
    competitors TEXT NOT NULL DEFAULT '',
    revenue_model TEXT NOT NULL,
    initial_budget REAL NOT NULL DEFAULT 0,
    skills_resources TEXT NOT NULL,
    has_customer_interviews TEXT NOT NULL DEFAULT 'unknown',
    customer_interviews INTEGER NOT NULL DEFAULT 0,
    problem_evidence TEXT NOT NULL DEFAULT 'unknown',
    willingness_to_pay TEXT NOT NULL DEFAULT 'unknown',
    prototype_tested TEXT NOT NULL DEFAULT 'unknown',
    demand_evidence TEXT NOT NULL DEFAULT '',
    ratings_json TEXT NOT NULL,
    report_json TEXT NOT NULL,
    score REAL NOT NULL,
    classification TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime'))
);
CREATE INDEX IF NOT EXISTS idx_evaluations_created_at ON evaluations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_evaluations_classification ON evaluations(classification);
"""


def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path or DEFAULT_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def database_session(db_path: str | Path | None = None):
    """Connection context that commits on success and always closes the connection."""
    conn = connect(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str | Path | None = None) -> None:
    with database_session(db_path) as conn:
        conn.executescript(SCHEMA)


def save_evaluation(data: dict[str, Any], report: dict[str, Any], db_path: str | Path | None = None) -> int:
    init_db(db_path)
    query = """INSERT INTO evaluations (
        idea_name, industry, description, problem, solution, target_customers,
        geographic_market, uvp, competitors, revenue_model, initial_budget,
        skills_resources, has_customer_interviews, customer_interviews,
        problem_evidence, willingness_to_pay, prototype_tested, demand_evidence,
        ratings_json, report_json, score, classification
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    values = (
        str(data.get("idea_name", "")).strip(), str(data.get("industry", "")).strip(),
        str(data.get("description", "")).strip(), str(data.get("problem", "")).strip(),
        str(data.get("solution", "")).strip(), str(data.get("target_customers", "")).strip(),
        str(data.get("geographic_market", "")).strip(), str(data.get("uvp", "")).strip(),
        str(data.get("competitors", "")).strip(), str(data.get("revenue_model", "")).strip(),
        float(data.get("initial_budget", 0) or 0), str(data.get("skills_resources", "")).strip(),
        str(data.get("has_customer_interviews", "unknown")), int(data.get("customer_interviews", 0) or 0),
        str(data.get("problem_evidence", "unknown")), str(data.get("willingness_to_pay", "unknown")),
        str(data.get("prototype_tested", "unknown")), str(data.get("demand_evidence", "")).strip(),
        json.dumps(data.get("ratings", {}), ensure_ascii=False),
        json.dumps(report, ensure_ascii=False), float(report["score"]), str(report["classification"]),
    )
    with database_session(db_path) as conn:
        cursor = conn.execute(query, values)
        return int(cursor.lastrowid)


def list_evaluations(db_path: str | Path | None = None) -> list[dict[str, Any]]:
    init_db(db_path)
    with database_session(db_path) as conn:
        rows = conn.execute("""SELECT id, idea_name, industry, target_customers, score,
            classification, created_at FROM evaluations ORDER BY id DESC""").fetchall()
    return [dict(row) for row in rows]


def get_evaluation(evaluation_id: int, db_path: str | Path | None = None) -> dict[str, Any] | None:
    init_db(db_path)
    with database_session(db_path) as conn:
        row = conn.execute("SELECT * FROM evaluations WHERE id = ?", (evaluation_id,)).fetchone()
    if row is None:
        return None
    result = dict(row)
    for source, target in (("ratings_json", "ratings"), ("report_json", "report")):
        try:
            result[target] = json.loads(result.pop(source))
        except (TypeError, json.JSONDecodeError):
            result[target] = {}
    return result


def delete_evaluation(evaluation_id: int, db_path: str | Path | None = None) -> bool:
    init_db(db_path)
    with database_session(db_path) as conn:
        cursor = conn.execute("DELETE FROM evaluations WHERE id = ?", (evaluation_id,))
        return cursor.rowcount > 0


def dashboard_metrics(db_path: str | Path | None = None) -> dict[str, Any]:
    init_db(db_path)
    with database_session(db_path) as conn:
        row = conn.execute("""SELECT COUNT(*) AS total,
            COALESCE(AVG(score), 0) AS average_score,
            SUM(CASE WHEN classification = 'Promising' THEN 1 ELSE 0 END) AS promising,
            SUM(CASE WHEN classification = 'Needs Further Validation' THEN 1 ELSE 0 END) AS needs_validation,
            SUM(CASE WHEN classification = 'High Uncertainty' THEN 1 ELSE 0 END) AS high_uncertainty
            FROM evaluations""").fetchone()
        dist_rows = conn.execute("""SELECT classification, COUNT(*) AS count
            FROM evaluations GROUP BY classification""").fetchall()
    distribution = {"Promising": 0, "Needs Further Validation": 0, "High Uncertainty": 0}
    for r in dist_rows:
        distribution[r["classification"]] = int(r["count"])
    return {
        "total": int(row["total"] or 0),
        "average_score": round(float(row["average_score"] or 0), 1),
        "promising": int(row["promising"] or 0),
        "needs_validation": int(row["needs_validation"] or 0),
        "high_uncertainty": int(row["high_uncertainty"] or 0),
        "distribution": distribution,
    }
