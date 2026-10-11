"""
Week 5 -> Week 8 bridge: turn the live chat log into a gradable evaluation CSV.

Every question students ask the pilot chatbot is stored in moodlebot.db. This
exports them in the same format evaluate.py produces, so you grade real student
questions with the SAME process (fill `human_verdict`, then run score.py).

Usage:
    python3 export_logs.py                       # everything
    python3 export_logs.py --sample 40           # random 40, reproducible (for manual grading)
    python3 export_logs.py --since 2026-10-01    # only newer than a date (ISO format)
    python3 export_logs.py --stats               # usage / latency / feedback summary only

Privacy: the export never contains student identifiers, only session ids.
"""

import argparse
import csv
import pathlib
import random
import statistics
from datetime import datetime

import db

RESULTS_DIR = pathlib.Path(__file__).parent / "results"
FIELDS = ["interaction_id", "session_id", "created_at", "topic", "question", "expected_answer_notes",
          "generated_answer", "retrieved_sources", "response_time_sec", "student_rating",
          "human_verdict", "human_notes"]


def to_eval_row(r: dict) -> dict:
    topics = [s.split("/")[0] for s in r["sources"]]
    topic = max(set(topics), key=topics.count) if topics else ""
    return {
        "interaction_id": r["id"], "session_id": r["session_id"], "created_at": r["created_at"],
        "topic": topic, "question": r["question"], "expected_answer_notes": "",
        "generated_answer": r["answer"], "retrieved_sources": "; ".join(r["sources"]),
        "response_time_sec": r["response_time_s"],
        "student_rating": {1: "up", -1: "down"}.get(r["rating"], ""),
        "human_verdict": "", "human_notes": "",
    }


def summarize(rows: list[dict]) -> dict:
    times = sorted(r["response_time_s"] for r in rows if r["response_time_s"] is not None)
    rated = [r["rating"] for r in rows if r["rating"] in (1, -1)]

    def pct(p):
        return times[min(len(times) - 1, int(round(p * (len(times) - 1))))] if times else None

    return {
        "questions": len(rows),
        "sessions": len({r["session_id"] for r in rows}),
        "avg_response_s": round(statistics.mean(times), 2) if times else None,
        "median_response_s": round(statistics.median(times), 2) if times else None,
        "p95_response_s": round(pct(0.95), 2) if times else None,
        "thumbs_up": rated.count(1),
        "thumbs_down": rated.count(-1),
        "unrated": len(rows) - len(rated),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since", help="ISO date/time, e.g. 2026-10-01")
    ap.add_argument("--course", help="only this Moodle course id")
    ap.add_argument("--sample", type=int, help="random sample size (reproducible)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--stats", action="store_true", help="print a usage summary and exit")
    ap.add_argument("--out", help="output filename inside results/")
    args = ap.parse_args()

    rows = db.get_interactions(since=args.since, course_id=args.course)
    if not rows:
        print("No logged interactions match. (Has anyone used the chatbot yet?)")
        return

    s = summarize(rows)
    print(f"{s['questions']} questions in {s['sessions']} sessions | response time: "
          f"avg {s['avg_response_s']}s, median {s['median_response_s']}s, p95 {s['p95_response_s']}s | "
          f"feedback: {s['thumbs_up']} up / {s['thumbs_down']} down / {s['unrated']} unrated")
    if args.stats:
        return

    if args.sample and args.sample < len(rows):
        rows = sorted(random.Random(args.seed).sample(rows, args.sample), key=lambda r: r["id"])
        print(f"Random sample of {len(rows)} selected (seed {args.seed}).")

    RESULTS_DIR.mkdir(exist_ok=True)
    out = RESULTS_DIR / (args.out or f"live_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(to_eval_row(r) for r in rows)
    print(f"Wrote {out}\nNext: fill in 'human_verdict' (correct/partial/incorrect), then:  python3 score.py {out}")


if __name__ == "__main__":
    main()
