"""MEASURE box of MAP.md: does a judge change its verdict on the same saved answer?

Judges the flipped answers from v0 run 1 and run 2 again. The answer text is fixed here,
so a verdict that changes shows judge noise, not answer noise.

Usage: python -m evals.stability
Makes (6 questions x 2 answers x RUNS) = 36 Gemini calls. Needs GOOGLE_API_KEY in .env.
"""
import json
from pathlib import Path

from evals.judge import RUNS, judge_correctness, judge_faithfulness

EVALS = Path(__file__).resolve().parent
RESULT_FILES = {"run1": EVALS / "results" / "v0.jsonl", "run2": EVALS / "results" / "v0_run2.jsonl"}
CORRECT_IDS = ["q02", "q30"]
FAITHFUL_IDS = ["q12", "q27", "q32", "q36"]


def load_rows(path):
    return {r["id"]: r for r in map(json.loads, path.read_text().splitlines())}


def load_expected():
    # From golden.jsonl, not the results files, so a fixed golden answer is used.
    rows = map(json.loads, (EVALS / "golden.jsonl").read_text().splitlines())
    return {r["id"]: r["answer"] for r in rows}


def check(label, judge):
    verdicts = [judge() for _ in range(RUNS)]
    labels = [v.label for v in verdicts]
    is_stable = len(set(labels)) == 1
    print(f"{label}  {'stable  ' if is_stable else 'UNSTABLE'}  {labels}", flush=True)
    return is_stable


def main():
    runs = {name: load_rows(path) for name, path in RESULT_FILES.items()}
    expected = load_expected()
    stable = total = 0
    for name, rows in runs.items():
        for qid in CORRECT_IDS:
            r = rows[qid]
            stable += check(f"{qid} correct  {name}",
                            lambda: judge_correctness(r["question"], expected[qid], r["answer"]))
            total += 1
        for qid in FAITHFUL_IDS:
            r = rows[qid]
            stable += check(f"{qid} faithful {name}", lambda: judge_faithfulness(r["context"], r["answer"]))
            total += 1
    print(f"stable across {RUNS} runs on the same answer: {stable}/{total}")


if __name__ == "__main__":
    main()
