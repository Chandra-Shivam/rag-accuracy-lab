"""MEASURE box of MAP.md: run the golden set and report metrics.

Retrieval metrics only so far (hit@k, MRR), so no Gemini calls. Generation metrics come next.
Usage: python evals/run.py            (all questions)
       python evals/run.py <case_id>  (one question)
Needs PINECONE_API_KEY in .env.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# "python evals/run.py" puts evals/ on the path, not the project root.
sys.path.insert(0, str(ROOT))

from evals.metrics import is_hit, reciprocal_rank
from rag.answer import K, retrieve

GOLDEN = ROOT / "evals" / "golden.jsonl"


def load_golden(case_id=None):
    rows = [json.loads(line) for line in GOLDEN.read_text().splitlines() if line.strip()]
    if case_id:
        rows = [q for q in rows if q["id"] == case_id]
        if not rows:
            sys.exit(f"no question with id {case_id!r}")
    return rows


def score_retrieval(questions, k=K):
    """One row per answerable question. Unanswerable ones are measured by abstention instead."""
    rows = []
    for q in questions:
        if q["type"] == "unanswerable":
            continue
        _, sources = retrieve(q["question"], k=k)
        rows.append({"id": q["id"], "type": q["type"], "gold": q["gold"], "sources": sources,
                     "hit": is_hit(q["gold"], sources), "rr": reciprocal_rank(q["gold"], sources)})
    return rows


def summary(rows):
    n = len(rows)
    return f"hit@{K} {sum(r['hit'] for r in rows) / n:.3f}  MRR {sum(r['rr'] for r in rows) / n:.3f}  (n={n})"


def report(rows):
    for r in rows:
        status = "hit " if r["hit"] else "MISS"
        gold = ", ".join(f"{g['source']} p{g['page']}" for g in r["gold"])
        print(f"{r['id']}  {status}  rr {r['rr']:.2f}  {r['type']:<11}  gold: {gold}")
        if not r["hit"]:
            got = ", ".join(f"{s['source']} p{s['page']}" for s in r["sources"])
            print(f"     retrieved: {got}")

    by_type = defaultdict(list)
    for r in rows:
        by_type[r["type"]].append(r)
    print()
    for type_name, group in sorted(by_type.items()):
        print(f"{type_name:<11}  {summary(group)}")
    print(f"{'ALL':<11}  {summary(rows)}")


if __name__ == "__main__":
    questions = load_golden(sys.argv[1] if len(sys.argv) > 1 else None)
    rows = score_retrieval(questions)
    if rows:
        report(rows)
    else:
        print("unanswerable question: not scored by retrieval metrics")
