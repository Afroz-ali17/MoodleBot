"""
Week 4 (and later, Week 13) — scores a graded evaluation CSV.

After you've run evaluate.py and filled in the 'human_verdict' column
(correct / partial / incorrect) for each row, run this to get an accuracy
breakdown — the same style of figure your abstract's 88% benchmark refers to.

Usage:
    python3 score.py results/eval_20260901_143000.csv
"""

import csv
import sys
import pathlib
from collections import Counter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 score.py <results_csv_path>")
        sys.exit(1)

    path = pathlib.Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    verdicts = [r["human_verdict"].strip().lower() for r in rows]
    graded = [v for v in verdicts if v]
    ungraded = len(rows) - len(graded)

    if ungraded:
        print(f"Warning: {ungraded} row(s) have no human_verdict filled in yet — "
              f"grade those before trusting this score.\n")

    counts = Counter(graded)
    total_graded = len(graded)

    if total_graded == 0:
        print("No graded rows yet. Fill in 'human_verdict' (correct/partial/incorrect) and re-run.")
        return

    correct = counts.get("correct", 0)
    partial = counts.get("partial", 0)
    incorrect = counts.get("incorrect", 0)
    other = total_graded - correct - partial - incorrect

    # Strict accuracy: correct only. Lenient: correct + partial counted half.
    strict_accuracy = correct / total_graded * 100
    lenient_accuracy = (correct + 0.5 * partial) / total_graded * 100

    print(f"Results: {path.name}")
    print(f"Total questions: {len(rows)} ({total_graded} graded)")
    print(f"  Correct:   {correct}")
    print(f"  Partial:   {partial}")
    print(f"  Incorrect: {incorrect}")
    if other:
        print(f"  Other/unrecognized verdict values: {other} (expected: correct/partial/incorrect)")
    print(f"\nStrict accuracy (correct only):        {strict_accuracy:.1f}%")
    print(f"Lenient accuracy (partial = half credit): {lenient_accuracy:.1f}%")
    print(f"\nTarget benchmark from project abstract: 88%")

    # Per-topic breakdown
    by_topic = {}
    for r in rows:
        v = r["human_verdict"].strip().lower()
        if not v:
            continue
        topic = r.get("topic", "unknown") or "unknown"
        by_topic.setdefault(topic, []).append(v)

    if by_topic:
        print("\nBy topic:")
        for topic, vs in sorted(by_topic.items()):
            c = vs.count("correct")
            pct = c / len(vs) * 100
            print(f"  {topic}: {c}/{len(vs)} correct ({pct:.0f}%)")


if __name__ == "__main__":
    main()
