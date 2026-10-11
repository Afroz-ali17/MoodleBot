"""
Week 5 API tests. Run from backend/:   pytest -q

A fake RAG pipeline replaces the real one, so these tests need no embedding
model, no vector store and no LLM key — they verify the API layer itself:
sessions, history, logging, auth, rate limiting, feedback, privacy.
"""

import importlib
import os
import sys
import pathlib

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))


class FakePipeline:
    def __init__(self):
        self.calls = []

    def answer(self, question, history=None):
        self.calls.append({"question": question, "history": history or []})
        return {"answer": f"echo: {question}", "sources": ["normalization/week4_notes.txt"]}


@pytest.fixture
def api(tmp_path, monkeypatch):
    monkeypatch.setenv("MOODLEBOT_DB", str(tmp_path / "test.db"))
    monkeypatch.delenv("MOODLEBOT_API_KEY", raising=False)
    monkeypatch.setenv("RATE_LIMIT_PER_MIN", "100")
    for mod in ("db", "main"):
        sys.modules.pop(mod, None)
    main = importlib.import_module("main")
    fake = FakePipeline()
    monkeypatch.setattr(main, "_get_pipeline", lambda: fake)
    return main, TestClient(main.app), fake


def ask(client, student="u1", q="What is 3NF?", session=None):
    body = {"student_id": student, "question": q}
    if session:
        body["session_id"] = session
    return client.post("/chat", json=body)


def test_health(api):
    _, client, _ = api
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_chat_creates_session_and_logs(api):
    main, client, _ = api
    r = ask(client)
    assert r.status_code == 200
    data = r.json()
    assert data["answer"] == "echo: What is 3NF?"
    assert len(data["session_id"]) >= 8 and data["interaction_id"] == 1
    with main.db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM interactions").fetchone()[0] == 1


def test_followup_receives_history(api):
    _, client, fake = api
    sid = ask(client, q="What is 3NF?").json()["session_id"]
    ask(client, q="give an example", session=sid)
    second_call = fake.calls[1]
    roles = [m["role"] for m in second_call["history"]]
    assert roles == ["user", "assistant"]
    assert second_call["history"][0]["content"] == "What is 3NF?"


def test_sessions_are_isolated_between_students(api):
    _, client, fake = api
    sid = ask(client, student="alice", q="alice secret question").json()["session_id"]
    # bob guesses alice's session id
    ask(client, student="bob", q="hello there bob", session=sid)
    assert fake.calls[1]["history"] == []
    # and cannot read her transcript
    # Bob's view of that session id contains only Bob's own message, never Alice's
    r = client.get(f"/history/{sid}", params={"student_id": "bob"})
    assert [m["question"] for m in r.json()["messages"]] == ["hello there bob"]
    r = client.get(f"/history/{sid}", params={"student_id": "alice"})
    assert [m["question"] for m in r.json()["messages"]] == ["alice secret question"]


def test_student_id_is_not_stored_in_plaintext(api):
    main, client, _ = api
    ask(client, student="moodle-user-4711")
    with main.db.connect() as conn:
        row = conn.execute("SELECT student_hash FROM interactions").fetchone()
    assert "4711" not in row["student_hash"] and len(row["student_hash"]) == 32


def test_api_key_required_when_configured(api, monkeypatch):
    _, client, _ = api
    monkeypatch.setenv("MOODLEBOT_API_KEY", "s3cret")
    assert ask(client).status_code == 401
    r = client.post("/chat", json={"student_id": "u1", "question": "hi there"},
                    headers={"X-API-Key": "wrong"})
    assert r.status_code == 401
    r = client.post("/chat", json={"student_id": "u1", "question": "hi there"},
                    headers={"X-API-Key": "s3cret"})
    assert r.status_code == 200


def test_rate_limit(api, monkeypatch):
    _, client, _ = api
    monkeypatch.setenv("RATE_LIMIT_PER_MIN", "3")
    codes = [ask(client, student="spammer").status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429]
    assert ask(client, student="someone-else").status_code == 200


def test_input_validation(api):
    _, client, _ = api
    assert client.post("/chat", json={"student_id": "u1", "question": ""}).status_code == 422
    assert client.post("/chat", json={"student_id": "u1", "question": "x" * 1001}).status_code == 422
    bad = client.post("/chat", json={"student_id": "u1", "question": "ok", "session_id": "../etc"})
    assert bad.status_code == 422


def test_feedback_flow(api):
    main, client, _ = api
    iid = ask(client, student="u1").json()["interaction_id"]
    ok = client.post("/feedback", json={"student_id": "u1", "interaction_id": iid, "rating": 1})
    assert ok.status_code == 200
    # someone else cannot rate u1's answer
    nope = client.post("/feedback", json={"student_id": "u2", "interaction_id": iid, "rating": -1})
    assert nope.status_code == 404
    bad = client.post("/feedback", json={"student_id": "u1", "interaction_id": iid, "rating": 5})
    assert bad.status_code == 422
    with main.db.connect() as conn:
        assert conn.execute("SELECT rating FROM interactions WHERE id=?", (iid,)).fetchone()[0] == 1


def test_pipeline_setup_error_maps_to_503(api, monkeypatch):
    main, client, _ = api

    class Broken:
        def answer(self, *a, **k):
            raise RuntimeError("Vector store not found")

    monkeypatch.setattr(main, "_get_pipeline", lambda: Broken())
    r = ask(client)
    assert r.status_code == 503 and "Vector store" in r.json()["detail"]


def test_pipeline_unexpected_error_maps_to_502(api, monkeypatch):
    main, client, _ = api

    class Broken:
        def answer(self, *a, **k):
            raise ConnectionError("llm provider down")

    monkeypatch.setattr(main, "_get_pipeline", lambda: Broken())
    assert ask(client).status_code == 502
