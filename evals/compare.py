"""MEASURE box of MAP.md: compare two saved runs, question by question.

Usage: python evals/compare.py v0 v0_run2
Reads evals/results/<run>.jsonl. Makes no Gemini calls.
Equal totals can hide flips, so this lists every question whose result changed.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# "python evals/compare.py" puts evals/ on the path, not the project root.
sys.path.insert(0, str(ROOT))

from evals.metrics import summarize

RESULTS = ROOT / "evals" / "results"
METRICS = ("hit", "rr", "correct", "faithful", "abstained")


def load_run(name):
    path = RESULTS / f"{name}.jsonl"
    if not path.exists():
        sys.exit(f"no results file: {path}")
    return {r["id"]: r for r in map(json.loads, path.read_text().splitlines())}


def find_flips(before, after, metric):
    """Returns (id, before value, after value) for questions scored in both runs whose value changed."""
    return [(qid, before[qid][metric], after[qid][metric]) for qid in sorted(before.keys() & after.keys())
            if metric in before[qid] and metric in after[qid] and before[qid][metric] != after[qid][metric]]


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: python evals/compare.py <run_a> <run_b>")
    name_a, name_b = sys.argv[1:]
    before, after = load_run(name_a), load_run(name_b)

    only_one = sorted(before.keys() ^ after.keys())
    if only_one:
        print(f"in only one run, not compared: {' '.join(only_one)}")

    shared = before.keys() & after.keys()
    summary_a = summarize([before[qid] for qid in shared])
    summary_b = summarize([after[qid] for qid in shared])
    print(f"{name_a} -> {name_b}, {len(shared)} questions")
    for metric in METRICS:
        if summary_a[metric] is None or summary_b[metric] is None:
            continue
        flips = find_flips(before, after, metric)
        print(f"{metric:<10} {summary_a[metric]:.3f} -> {summary_b[metric]:.3f}  flips {len(flips)}")
        for qid, value_a, value_b in flips:
            print(f"  {qid}  {value_a} -> {value_b}")


if __name__ == "__main__":
    main()
