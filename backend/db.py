"""
Week 5 — persistence layer (SQLite, Python stdlib only).

One table, `interactions`, holds every question/answer pair. It does double
duty:
  * conversation history  -> rows with the same session_id, oldest first
  * evaluation log        -> exported in Week 8 for accuracy scoring

Students are stored only as a salted SHA-256 hash (see main.py), never as a
Moodle user id, to respect the privacy requirement (NFR-6).
"""

import json
import os
import pathlib
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

def get_db_path() -> pathlib.Path:
    return pathlib.Path(os.environ.get("MOODLEBOT_DB", pathlib.Path(__file__).parent / "moodlebot.db"))


DB_PATH = get_db_path()

SCHEMA = """
CREATE TABLE IF NOT EXISTS interactions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id       TEXT NOT NULL,
    student_hash     TEXT NOT NULL,
    course_id        TEXT,
    question         TEXT NOT NULL,
    answer           TEXT NOT NULL,
    sources          TEXT NOT NULL DEFAULT '[]',   -- JSON list
    response_time_s  REAL,
    rating           INTEGER,                      -- +1 helpful / -1 not helpful
    feedback_comment TEXT,
    created_at       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_interactions_session ON interactions(session_id, id);
"""


@contextmanager
def connect():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.executescript(SCHEMA)


def log_interaction(session_id: str, student_hash: str, course_id: str | None,
                    question: str, answer: str, sources: list[str],
                    response_time_s: float) -> int:
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO interactions
               (session_id, student_hash, course_id, question, answer, sources,
                response_time_s, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (session_id, student_hash, course_id, question, answer,
             json.dumps(sources), round(response_time_s, 3),
             datetime.now(timezone.utc).isoformat()),
        )
        return cur.lastrowid


def get_history(session_id: str, student_hash: str, limit: int = 8) -> list[dict]:
    """Last `limit` exchanges of a session as LLM-style messages, oldest first.
    Scoped to student_hash so one student can never read another's session."""
    with connect() as conn:
        rows = conn.execute(
            """SELECT question, answer FROM interactions
               WHERE session_id = ? AND student_hash = ?
               ORDER BY id DESC LIMIT ?""",
            (session_id, student_hash, limit),
        ).fetchall()
    messages = []
    for r in reversed(rows):
        messages.append({"role": "user", "content": r["question"]})
        messages.append({"role": "assistant", "content": r["answer"]})
    return messages


def get_session_transcript(session_id: str, student_hash: str) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """SELECT id, question, answer, sources, rating, created_at
               FROM interactions WHERE session_id = ? AND student_hash = ?
               ORDER BY id""",
            (session_id, student_hash),
        ).fetchall()
    return [
        {"interaction_id": r["id"], "question": r["question"], "answer": r["answer"],
         "sources": json.loads(r["sources"]), "rating": r["rating"],
         "timestamp": r["created_at"]}
        for r in rows
    ]


def set_feedback(interaction_id: int, student_hash: str, rating: int, comment: str | None) -> bool:
    """Returns False if the interaction doesn't exist or belongs to someone else."""
    with connect() as conn:
        cur = conn.execute(
            """UPDATE interactions SET rating = ?, feedback_comment = ?
               WHERE id = ? AND student_hash = ?""",
            (rating, comment, interaction_id, student_hash),
        )
        return cur.rowcount == 1


def get_interactions(since: str | None = None, course_id: str | None = None,
                     include_smoke_tests: bool = False) -> list[dict]:
    """All logged exchanges, oldest first, for export/analysis. Student identity is
    never included (only the salted hash exists in the DB, and it is not returned)."""
    query = ("SELECT id, session_id, course_id, question, answer, sources, response_time_s, "
             "rating, feedback_comment, created_at FROM interactions WHERE 1=1")
    params: list = []
    if since:
        query += " AND created_at >= ?"
        params.append(since)
    if course_id:
        query += " AND course_id = ?"
        params.append(course_id)
    if not include_smoke_tests:
        query += " AND (course_id IS NULL OR course_id != 'smoke-test')"
    query += " ORDER BY id"
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r, sources=json.loads(r["sources"])) for r in rows]
