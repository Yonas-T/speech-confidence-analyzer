"""
SQLite database layer for Speaker Confidence sessions.
Stores session summaries and per-timestamp data points.
"""

import sqlite3
import os
from pathlib import Path

# Database lives at src/data/sessions.db
DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DB_DIR / "sessions.db"


def _get_connection():
    """Return a connection with row_factory set to sqlite3.Row."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables if they don't already exist."""
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            name TEXT,
            date TEXT,
            duration INTEGER,
            avg_confidence REAL,
            max_confidence REAL,
            min_confidence REAL,
            time_high INTEGER,
            time_medium INTEGER,
            time_low INTEGER,
            avg_visibility REAL,
            avg_posture_straightness REAL,
            avg_body_orientation REAL,
            avg_hand_openness REAL,
            avg_gesture_activity REAL,
            avg_head_position REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_points (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            timestamp INTEGER,
            confidence REAL,
            visibility REAL,
            posture_straightness REAL,
            body_orientation REAL,
            hand_openness REAL,
            gesture_activity REAL,
            head_position REAL,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


def save_session(session_data: dict):
    """
    Persist a complete session.

    session_data must contain:
        id, name, date, duration,
        avg_confidence, max_confidence, min_confidence,
        time_high, time_medium, time_low,
        avg_visibility, avg_posture_straightness, avg_body_orientation,
        avg_hand_openness, avg_gesture_activity, avg_head_position,
        data_points: list of dicts with
            timestamp, confidence, visibility, posture_straightness,
            body_orientation, hand_openness, gesture_activity, head_position
    """
    conn = _get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO sessions (
            id, name, date, duration,
            avg_confidence, max_confidence, min_confidence,
            time_high, time_medium, time_low,
            avg_visibility, avg_posture_straightness, avg_body_orientation,
            avg_hand_openness, avg_gesture_activity, avg_head_position
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_data["id"],
        session_data["name"],
        session_data["date"],
        session_data["duration"],
        session_data["avg_confidence"],
        session_data["max_confidence"],
        session_data["min_confidence"],
        session_data["time_high"],
        session_data["time_medium"],
        session_data["time_low"],
        session_data["avg_visibility"],
        session_data["avg_posture_straightness"],
        session_data["avg_body_orientation"],
        session_data["avg_hand_openness"],
        session_data["avg_gesture_activity"],
        session_data["avg_head_position"],
    ))

    for dp in session_data.get("data_points", []):
        cursor.execute("""
            INSERT INTO data_points (
                session_id, timestamp, confidence,
                visibility, posture_straightness, body_orientation,
                hand_openness, gesture_activity, head_position
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_data["id"],
            dp["timestamp"],
            dp["confidence"],
            dp["visibility"],
            dp["posture_straightness"],
            dp["body_orientation"],
            dp["hand_openness"],
            dp["gesture_activity"],
            dp["head_position"],
        ))

    conn.commit()
    conn.close()


def get_all_sessions() -> list[dict]:
    """Return every session as a list of dicts (no data_points)."""
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM sessions ORDER BY date DESC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_session(session_id: str) -> dict | None:
    """Return a single session dict with its data_points list, or None."""
    conn = _get_connection()

    row = conn.execute(
        "SELECT * FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()

    if row is None:
        conn.close()
        return None

    session = dict(row)

    dp_rows = conn.execute(
        "SELECT * FROM data_points WHERE session_id = ? ORDER BY timestamp",
        (session_id,),
    ).fetchall()

    session["data_points"] = [dict(r) for r in dp_rows]
    conn.close()
    return session


def delete_session(session_id: str) -> bool:
    """Delete a session and its data points. Return True if a row was deleted."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted
