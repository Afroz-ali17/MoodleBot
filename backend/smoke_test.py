"""
One-command check that the backend is up and behaves, from the machine that will
serve the pilot. Uses only the Python standard library.

    python3 smoke_test.py                              # http://localhost:8000
    python3 smoke_test.py --url http://192.168.1.20:8000

Reads MOODLEBOT_API_KEY from backend/.env or the environment (same secret you
pasted into the Moodle plugin settings). Calls /chat once, so it needs the vector
store built and GROK_API_KEY set; the logged exchange is tagged course_id
"smoke-test" and excluded from evaluation exports.
"""

import argparse
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

try:
    from dotenv import load_dotenv
    load_dotenv(pathlib.Path(__file__).parent / ".env")
except ImportError:
    pass

failures = 0


def call(base, method, path, key, payload=None, timeout=90):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(base + path, data=data, method=method,
                                 headers={"Content-Type": "application/json", **({"X-API-Key": key} if key else {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}
    except Exception as e:
        return 0, {"detail": str(e)}


def check(label, ok, detail=""):
    global failures
    print(("  PASS  " if ok else "  FAIL  ") + label + (f"   [{detail}]" if detail and not ok else ""))
    failures += 0 if ok else 1
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000")
    base = ap.parse_args().url.rstrip("/")
    key = os.environ.get("MOODLEBOT_API_KEY", "")

    status, health = call(base, "GET", "/health", key)
    if not check(f"API reachable at {base}", status == 200, str(health)):
        sys.exit(1)
    check("vector store built (ran ingest.py)", health.get("vector_store_ready") is True,
          "run `python3 ingest.py` first")
    if health.get("auth_enabled"):
        s, _ = call(base, "POST", "/chat", "wrong-key", {"student_id": "x", "question": "hi"})
        check("requests without the right API key are rejected (401)", s == 401, f"got {s}")
        check("MOODLEBOT_API_KEY available to this script", bool(key), "set it in backend/.env")
    else:
        print("  WARN  API key auth is OFF — set MOODLEBOT_API_KEY before the student pilot")

    student = {"student_id": "smoke-test", "course_id": "smoke-test"}
    t0 = time.perf_counter()
    s, d = call(base, "POST", "/chat", key, {**student, "question": "What is normalization?"})
    took = time.perf_counter() - t0
    if not check("chat returns an answer", s == 200 and bool(d.get("answer")), f"{s} {d}"):
        hints = {
            401: "MOODLEBOT_API_KEY is missing or differs from the one the server was started with.",
            422: "The request was rejected as invalid — is this script up to date with main.py?",
            429: "Rate limit hit — wait a minute (or raise RATE_LIMIT_PER_MIN) and retry.",
            503: "Setup problem: vector store missing (run ingest.py) or GROK_API_KEY not set in backend/.env.",
            502: "The pipeline failed: no internet (embedding model / Grok API), or an invalid GROK_API_KEY.",
            0: "Connection dropped mid-request or timed out (the first call can be slow while the model loads).",
        }
        print("         Hint: " + hints.get(s, f"unexpected status {s}; see the uvicorn terminal for the traceback"))
        sys.exit(1)
    print(f"         answer: {d['answer'][:110].strip()}...\n         sources: {d['sources']}  ({took:.1f}s)")
    check("response time within the 5s target (first call may be slower: model warm-up)", took <= 5,
          f"{took:.1f}s")
    check("answer cites at least one course source", len(d["sources"]) > 0)

    s2, d2 = call(base, "POST", "/chat", key, {**student, "question": "give an example", "session_id": d["session_id"]})
    check("follow-up in the same session works", s2 == 200 and bool(d2.get("answer")), f"{s2} {d2}")
    s3, h = call(base, "GET", f"/history/{d['session_id']}?student_id=smoke-test", key)
    check("session history stored (2 exchanges)", s3 == 200 and len(h.get("messages", [])) == 2, f"{s3} {h}")
    s4, _ = call(base, "POST", "/feedback", key, {"student_id": "smoke-test", "interaction_id": d["interaction_id"], "rating": 1})
    check("feedback recorded", s4 == 200, str(s4))

    print("\nAll checks passed — ready to connect Moodle." if not failures else f"\n{failures} check(s) failed.")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
