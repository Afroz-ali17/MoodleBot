"""
Week 4 — RAG evaluation harness.

Runs every question in test_questions.csv through the RAG pipeline and
writes out a results file you can manually grade, plus prints a live
summary as it goes.

Usage:
    python3 evaluate.py
    python3 evaluate.py --questions my_other_questions.csv --out run2.csv

Workflow:
    1. Fill in / expand test_questions.csv with real questions from your
       course (aim for 15-30+ covering every topic — the 8 provided are
       just a starting template).
    2. Run this script. It writes results/<timestamp>.csv with each
       question's generated answer, retrieved sources, and an empty
       'human_verdict' column.
    3. Open that CSV and fill in human_verdict as correct / partial /
       incorrect for each row (this is what your 88% accuracy figure
       will ultimately come from — see also score.py).
    4. If accuracy or groundedness looks weak, tune CHUNK_SIZE_WORDS /
       CHUNK_OVERLAP_WORDS in ingest.py or TOP_K in rag_chain.py, re-run
       ingest.py, and re-run this script to compare.
"""

import argparse
import csv
import pathlib
import sys
import time
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from rag_chain import get_pipeline

BACKEND_DIR = pathlib.Path(__file__).parent
RESULTS_DIR = BACKEND_DIR / "results"


def load_questions(path: pathlib.Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", default="test_questions.csv")
    parser.add_argument("--out", default=None, help="Output filename (default: timestamped)")
    args = parser.parse_args()

    questions_path = BACKEND_DIR / args.questions
    if not questions_path.exists():
        print(f"Questions file not found: {questions_path}")
        return

    questions = load_questions(questions_path)
    if not questions:
        print("No questions found in the CSV.")
        return

    print(f"Loaded {len(questions)} test question(s) from {questions_path.name}")
    pipeline = get_pipeline()

    RESULTS_DIR.mkdir(exist_ok=True)
    out_name = args.out or f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    out_path = RESULTS_DIR / out_name

    rows = []
    for i, q in enumerate(questions, 1):
        question_text = q["question"]
        print(f"\n[{i}/{len(questions)}] {question_text}", flush=True)

        result = None
        elapsed = 0
        error_msg = None

        for attempt in range(4):
            start = time.time()
            try:
                result = pipeline.answer(question_text)
                elapsed = round(time.time() - start, 2)
                error_msg = None
                break
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "rate_limit" in error_msg.lower():
                    wait_sec = 3 * (attempt + 1)
                    print(f"  -> Rate limit encountered, waiting {wait_sec}s before retry {attempt + 1}/3...", flush=True)
                    time.sleep(wait_sec)
                else:
                    break

        if result is not None:
            print(f"  -> {result['answer'][:150]}{'...' if len(result['answer']) > 150 else ''}", flush=True)
            print(f"  -> sources: {result['sources']} | {elapsed}s", flush=True)
            rows.append({
                "topic": q.get("topic", ""),
                "question": question_text,
                "expected_answer_notes": q.get("expected_answer_notes", ""),
                "generated_answer": result["answer"],
                "retrieved_sources": "; ".join(result["sources"]),
                "response_time_sec": elapsed,
                "human_verdict": "",   # fill in: correct / partial / incorrect
                "human_notes": "",
            })
        else:
            print(f"  -> ERROR: {error_msg}", flush=True)
            rows.append({
                "topic": q.get("topic", ""),
                "question": question_text,
                "expected_answer_notes": q.get("expected_answer_notes", ""),
                "generated_answer": f"[ERROR] {error_msg}",
                "retrieved_sources": "",
                "response_time_sec": "",
                "human_verdict": "",
                "human_notes": "",
            })

        # Polite 2-second pause between questions to stay under Groq free-tier 30 RPM limit
        time.sleep(2)

    fieldnames = ["topic", "question", "expected_answer_notes", "generated_answer",
                  "retrieved_sources", "response_time_sec", "human_verdict", "human_notes"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n\nDone. Results written to {out_path}")
    print("Next: open this CSV, fill in 'human_verdict' for each row (correct/partial/incorrect),")
    print("then run: python3 score.py results/" + out_name)


if __name__ == "__main__":
    main()
