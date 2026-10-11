"""Tests for the Week 5 log export, privacy guarantees and start-up behaviour."""

import csv
import importlib
import sys
import pathlib

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("MOODLEBOT_DB", str(tmp_path / "t.db"))
    monkeypatch.delenv("MOODLEBOT_API_KEY", raising=False)
    monkeypatch.setenv("RATE_LIMIT_PER_MIN", "1000")
    monkeypatch.setenv("MOODLEBOT_SKIP_WARMUP", "1")
    for mod in ("db", "main", "export_logs"):
        sys.modules.pop(mod, None)
    main = importlib.import_module("main")

    class Fake:
        def answer(self, q, history=None):
            return {"answer": f"a:{q}", "sources": ["sql/joins.txt", "sql/group.txt", "er/e.txt"]}

    monkeypatch.setattr(main, "_get_pipeline", lambda: Fake())
    return main, TestClient(main.app), importlib.import_module("export_logs"), importlib.import_module("db")


def ask(client, student, q, course="7", session=None):
    body = {"student_id": student, "question": q, "course_id": course}
    if session:
        body["session_id"] = session
    return client.post("/chat", json=body).json()


def test_export_rows_are_gradable_and_anonymous(env):
    main, client, export, db = env
    first = ask(client, "student-1", "What is a join?")
    client.post("/feedback", json={"student_id": "student-1", "interaction_id": first["interaction_id"], "rating": -1})

    rows = [export.to_eval_row(r) for r in db.get_interactions()]
    assert len(rows) == 1
    row = rows[0]
    assert row["topic"] == "sql"                     # most common source topic
    assert row["student_rating"] == "down"
    assert row["human_verdict"] == "" and row["generated_answer"] == "a:What is a join?"
    assert set(row) == set(export.FIELDS)
    # privacy: nothing in the export can identify the student
    dump = repr(rows) + repr(db.get_interactions())
    assert "student-1" not in dump and main.hash_student("student-1") not in dump


def test_export_csv_is_compatible_with_score_py(env, tmp_path):
    _, client, export, db = env
    ask(client, "a", "q1"); ask(client, "b", "q2")
    path = tmp_path / "live.csv"
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=export.FIELDS)
        w.writeheader()
        for r in db.get_interactions():
            row = export.to_eval_row(r)
            row["human_verdict"] = "correct"
            w.writerow(row)
    import subprocess
    out = subprocess.run([sys.executable, str(pathlib.Path(export.__file__).parent / "score.py"), str(path)],
                         capture_output=True, text=True)
    assert out.returncode == 0 and "Strict accuracy (correct only):        100.0%" in out.stdout


def test_smoke_test_traffic_is_excluded_from_exports(env):
    _, client, _, db = env
    ask(client, "smoke-test", "What is normalization?", course="smoke-test")
    ask(client, "real", "What is SQL?", course="7")
    assert [r["question"] for r in db.get_interactions()] == ["What is SQL?"]
    assert len(db.get_interactions(include_smoke_tests=True)) == 2


def test_filters_by_course_and_date(env):
    _, client, _, db = env
    ask(client, "a", "in course 7", course="7"); ask(client, "a", "in course 9", course="9")
    assert [r["question"] for r in db.get_interactions(course_id="9")] == ["in course 9"]
    assert db.get_interactions(since="2999-01-01") == []


def test_summary_statistics(env):
    _, client, export, db = env
    for i in range(3):
        d = ask(client, "s", f"q{i}")
    client.post("/feedback", json={"student_id": "s", "interaction_id": d["interaction_id"], "rating": 1})
    s = export.summarize(db.get_interactions())
    assert (s["questions"], s["sessions"], s["thumbs_up"], s["thumbs_down"], s["unrated"]) == (3, 3, 1, 0, 2)
    assert s["p95_response_s"] >= s["median_response_s"] >= 0


def test_sample_is_reproducible_and_does_not_exceed_log(env):
    import random
    _, client, _, db = env
    for i in range(20):
        ask(client, "s", f"q{i}")
    rows = db.get_interactions()
    a = random.Random(42).sample(rows, 5); b = random.Random(42).sample(rows, 5)
    assert [r["id"] for r in a] == [r["id"] for r in b]


def test_failing_warmup_does_not_prevent_the_api_from_serving(tmp_path, monkeypatch):
    """No vector store / no internet at start-up must not crash the server."""
    monkeypatch.setenv("MOODLEBOT_DB", str(tmp_path / "w.db"))
    monkeypatch.delenv("MOODLEBOT_SKIP_WARMUP", raising=False)
    for mod in ("db", "main"):
        sys.modules.pop(mod, None)
    main = importlib.import_module("main")

    class Broken:
        def warmup(self):
            raise RuntimeError("Vector store not found")

    monkeypatch.setattr(main, "_get_pipeline", lambda: Broken())
    with TestClient(main.app) as client:          # context manager runs the lifespan
        assert client.get("/health").status_code == 200
