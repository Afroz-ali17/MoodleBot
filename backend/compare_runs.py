"""
compare_runs.py — Side-by-side accuracy comparison tool for MoodleBot.

Compares two evaluation runs to demonstrate the empirical before-vs-after
accuracy improvement achieved through RAG hyperparameter tuning and prompt refinement.

Usage:
    python compare_runs.py [baseline_csv] [tuned_csv]
"""

import sys
import pathlib
import pandas as pd


def compute_metrics(csv_path: pathlib.Path) -> dict:
    if not csv_path.exists():
        raise FileNotFoundError(f"File not found: {csv_path}")

    df = pd.read_csv(csv_path)
    if "human_verdict" not in df.columns:
        raise ValueError(f"{csv_path} does not have 'human_verdict' column.")

    valid_df = df[df["human_verdict"].str.strip().str.lower().isin(["correct", "partial", "incorrect"])].copy()
    total = len(valid_df)
    if total == 0:
        return {"total": 0, "correct": 0, "partial": 0, "incorrect": 0, "strict": 0.0, "lenient": 0.0, "topics": {}}

    verdicts = valid_df["human_verdict"].str.strip().str.lower()
    correct = int((verdicts == "correct").sum())
    partial = int((verdicts == "partial").sum())
    incorrect = int((verdicts == "incorrect").sum())

    strict_acc = (correct / total) * 100.0
    lenient_acc = ((correct + 0.5 * partial) / total) * 100.0

    # Topic breakdown
    topics = {}
    for topic, group in valid_df.groupby("topic"):
        t_tot = len(group)
        t_cor = int((group["human_verdict"].str.strip().str.lower() == "correct").sum())
        t_pct = (t_cor / t_tot) * 100.0 if t_tot > 0 else 0.0
        topics[topic] = {"correct": t_cor, "total": t_tot, "pct": t_pct}

    return {
        "filename": csv_path.name,
        "total": total,
        "correct": correct,
        "partial": partial,
        "incorrect": incorrect,
        "strict": strict_acc,
        "lenient": lenient_acc,
        "topics": topics,
    }


def print_comparison(baseline_path: pathlib.Path, tuned_path: pathlib.Path):
    b = compute_metrics(baseline_path)
    t = compute_metrics(tuned_path)

    print("\n" + "=" * 76)
    print("        MOODLEBOT BENCHMARK: BEFORE VS AFTER TUNING COMPARISON")
    print("=" * 76)
    print(f"{'Evaluation Run:':<24} {'Baseline Run':<24} {'Tuned (Final) Run':<24}")
    print(f"{'Artifact File:':<24} {b['filename']:<24} {t['filename']:<24}")
    print("-" * 76)
    print(f"{'Metric':<24} {'Before Tuning':<20} {'After Tuning':<20} {'Improvement':<12}")
    print("-" * 76)

    # Core metrics
    delta_strict = t["strict"] - b["strict"]
    delta_lenient = t["lenient"] - b["lenient"]
    sign_s = "+" if delta_strict >= 0 else ""
    sign_l = "+" if delta_lenient >= 0 else ""

    print(f"{'Strict Accuracy':<24} {b['strict']:>5.1f}%{'':<14} {t['strict']:>5.1f}%{'':<14} {sign_s}{delta_strict:>4.1f}%")
    print(f"{'Lenient Accuracy':<24} {b['lenient']:>5.1f}%{'':<14} {t['lenient']:>5.1f}%{'':<14} {sign_l}{delta_lenient:>4.1f}%")
    print(f"{'Abstract Benchmark':<24} {'88.0%':<20} {'88.0%':<20} {'Exceeded' if t['strict'] >= 88 else ''}")
    print(f"{'Total Questions':<24} {b['total']:<20} {t['total']:<20} {'Balanced'}")
    cor_diff = f"+{t['correct'] - b['correct']}" if t['correct'] >= b['correct'] else str(t['correct'] - b['correct'])
    part_diff = str(t['partial'] - b['partial'])
    inc_diff = str(t['incorrect'] - b['incorrect'])

    print(f"{'  - Correct Answers':<24} {b['correct']:<20} {t['correct']:<20} {cor_diff}")
    print(f"{'  - Partial Credit':<24} {b['partial']:<20} {t['partial']:<20} {part_diff}")
    print(f"{'  - Incorrect Answers':<24} {b['incorrect']:<20} {t['incorrect']:<20} {inc_diff}")

    print("-" * 76)
    print("PER-TOPIC STRICT ACCURACY COMPARISON:")
    print("-" * 76)
    print(f"{'Topic':<24} {'Before Tuning':<20} {'After Tuning':<20} {'Delta'}")
    print("-" * 76)

    all_topics = sorted(set(b["topics"].keys()) | set(t["topics"].keys()))
    for top in all_topics:
        b_top = b["topics"].get(top, {"correct": 0, "total": 0, "pct": 0.0})
        t_top = t["topics"].get(top, {"correct": 0, "total": 0, "pct": 0.0})
        b_str = f"{b_top['correct']}/{b_top['total']} ({b_top['pct']:.0f}%)"
        t_str = f"{t_top['correct']}/{t_top['total']} ({t_top['pct']:.0f}%)"
        d = t_top["pct"] - b_top["pct"]
        d_str = f"+{d:.0f}%" if d > 0 else (f"{d:.0f}%" if d < 0 else "0%")
        print(f"{top:<24} {b_str:<20} {t_str:<20} {d_str}")

    print("=" * 76 + "\n")


if __name__ == "__main__":
    base_dir = pathlib.Path(__file__).parent / "results"
    
    # Defaults to the two comparison runs if not passed via CLI
    baseline = base_dir / "run2_tuned.csv"
    final = base_dir / "eval_20260907_223410.csv"

    if len(sys.argv) >= 3:
        baseline = pathlib.Path(sys.argv[1])
        final = pathlib.Path(sys.argv[2])
    elif len(sys.argv) == 2:
        final = pathlib.Path(sys.argv[1])

    print_comparison(baseline, final)
