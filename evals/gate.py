"""MEASURE box of MAP.md: fail loudly if a saved run is incomplete or below the minimum scores.

Usage: python evals/gate.py v6_prompt_fixes
Reads evals/results/<run>.jsonl. Makes no Gemini calls. Exit code 0 = pass, 1 = fail, so CI can read it.
Completeness is checked first: a run with missing questions can't pass, however good its numbers look.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# "python evals/gate.py" puts evals/ on the path, not the project root.
sys.path.insert(0, str(ROOT))

from evals.metrics import summarize
from rag.answer import is_refusal

GOLDEN = ROOT / "evals" / "golden.jsonl"
RESULTS = ROOT / "evals" / "results"
# Scores each row must have. summarize() skips rows without a field, so a missing one would shrink the total silently.
REQUIRED = {"answerable": ("hit", "evidence", "correct"), "unanswerable": ("abstained",)}
# Lowest share (0 to 1) of passing rows for each metric.
# Each minimum is the low end of v6's two runs: anything higher would fail on noise alone.
# v6: Correct 34-37/39, Abstain 10-11/11, Faithful 38/38 and 39/39 (exact refusals aren't judged).
# Faithful allows one fail, for a judge false fail: about 38 answers are judged, and 37/38 also lets 38/39 pass.
MINIMUMS = {"correct": 34 / 39, "abstained": 10 / 11, "faithful": 37 / 38}


def load_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def check_complete(golden, rows):
    """Every golden question has exactly one row, and every row has the scores its type needs."""
    problems = []
    expected = {q["id"] for q in golden}
    ids = [r["id"] for r in rows]
    if missing := sorted(expected - set(ids)):
        problems.append(f"missing questions: {', '.join(missing)}")
    if duplicates := sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"duplicate questions: {', '.join(duplicates)}")
    if unknown := sorted(set(ids) - expected):
        problems.append(f"questions not in the golden set: {', '.join(unknown)}")

    types = {q["id"]: q["type"] for q in golden}
    absent = {}  # score -> ids of the rows without it, so one line per score, not per row
    for r in rows:
        if r["id"] not in types:
            continue
        needed = REQUIRED["unanswerable" if types[r["id"]] == "unanswerable" else "answerable"]
        # Exact refusals skip the faithfulness judge (rag/answer.py), so only other answers need it.
        if not is_refusal(r.get("answer", "")):
            needed += ("faithful",)
        for key in needed:
            if key not in r:
                absent.setdefault(key, []).append(r["id"])
    for key, ids in absent.items():
        problems.append(f"no {key} on {len(ids)} rows: {', '.join(ids)}")
    return problems


def check_minimums(rows, minimums):
    """Each metric's share of passing rows is at least its minimum."""
    if not minimums:
        # An empty gate would pass every run, which is the silent pass this file exists to stop.
        return ["no minimums set"]
    scores = summarize(rows)
    problems = []
    for metric, minimum in minimums.items():
        score = scores.get(metric)
        if score is None:
            problems.append(f"{metric}: no rows have it")
        elif score < minimum:
            problems.append(f"{metric}: {score:.3f} is below the minimum {minimum:.3f}")
    return problems


def gate(golden, rows, minimums):
    """Returns the problems found; an empty list means the run passes."""
    # Scores of an incomplete run aren't checked: its numbers can't be trusted either way.
    return check_complete(golden, rows) or check_minimums(rows, minimums)


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python evals/gate.py <run>")
    path = RESULTS / f"{sys.argv[1]}.jsonl"
    if not path.exists():
        sys.exit(f"FAIL  no run file at {path}")
    problems = gate(load_jsonl(GOLDEN), load_jsonl(path), MINIMUMS)
    for problem in problems:
        print(f"  {problem}")
    print(f"{'FAIL' if problems else 'PASS'}  {sys.argv[1]}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
