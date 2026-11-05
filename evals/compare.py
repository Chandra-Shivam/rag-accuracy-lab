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
METRICS = ("hit", "rr", "evidence", "correct", "faithful", "abstained", "citations_ok")


def load_run(name):
    path = RESULTS / f"{name}.jsonl"
    if not path.exists():
        sys.exit(f"no results file: {path}")
    return {r["id"]: r for r in map(json.loads, path.read_text().splitlines())}


def scored_in_both(before, after, metric):
    """Questions with this metric in both runs. Exact refusals have no faithful score from v6 on."""
    return sorted(qid for qid in before.keys() & after.keys() if metric in before[qid] and metric in after[qid])


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
    print(f"{name_a} -> {name_b}, {len(shared)} questions")
    for metric in METRICS:
        scored = scored_in_both(before, after, metric)
        if not scored:
            continue
        mean_a = summarize([before[qid] for qid in scored])[metric]
        mean_b = summarize([after[qid] for qid in scored])[metric]
        flips = find_flips(before, after, metric)
        print(f"{metric:<10} {mean_a:.3f} -> {mean_b:.3f}  n={len(scored)}  flips {len(flips)}")
        for qid, value_a, value_b in flips:
            print(f"  {qid}  {value_a} -> {value_b}")


if __name__ == "__main__":
    main()
