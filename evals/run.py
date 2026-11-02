"""MEASURE box of MAP.md: run the golden set and report metrics.

Usage: python evals/run.py                     (all questions, saved to evals/results/v0.jsonl)
       python evals/run.py --run v0_run2       (same, saved under another name)
       python evals/run.py <case_id>           (one question, not saved)
       python evals/run.py --retrieval-only    (hit@k and MRR only, no Gemini calls, not saved)
A full run makes about 150 Gemini calls. If it stops (e.g. daily quota), the same command
continues it, skipping the questions already saved.
Needs GOOGLE_API_KEY and PINECONE_API_KEY in .env.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# "python evals/run.py" puts evals/ on the path, not the project root.
sys.path.insert(0, str(ROOT))

from evals.judge import judge_abstention, judge_correctness, judge_faithfulness
from evals.metrics import is_hit, reciprocal_rank, summarize
from rag.answer import K, answer, retrieve

GOLDEN = ROOT / "evals" / "golden.jsonl"
RESULTS = ROOT / "evals" / "results"


def load_golden(case_id=None):
    rows = [json.loads(line) for line in GOLDEN.read_text().splitlines() if line.strip()]
    if case_id:
        rows = [q for q in rows if q["id"] == case_id]
        if not rows:
            sys.exit(f"no question with id {case_id!r}")
    return rows


def score_retrieval(q):
    """Retrieval metrics for one answerable question. Needs no LLM."""
    _, sources = retrieve(q["question"])
    return {"id": q["id"], "type": q["type"], "sources": sources,
            "hit": is_hit(q["gold"], sources), "rr": reciprocal_rank(q["gold"], sources)}


def score_question(q):
    """Runs one question through the system and the judges that apply to its type."""
    result = answer(q["question"])
    faithful = judge_faithfulness(result["context"], result["answer"])
    row = {"id": q["id"], "type": q["type"], "question": q["question"], "expected": q["answer"],
           "answer": result["answer"], "context": result["context"], "sources": result["sources"],
           "latency": result["latency"], "tokens": result["tokens"],
           "faithful": faithful.label == "supported", "faithful_reason": faithful.reason}

    if q["type"] == "unanswerable":
        abstention = judge_abstention(q["question"], result["answer"])
        row.update(abstained=abstention.label == "abstained", abstained_reason=abstention.reason)
    else:
        correctness = judge_correctness(q["question"], q["answer"], result["answer"])
        row.update(hit=is_hit(q["gold"], result["sources"]), rr=reciprocal_rank(q["gold"], result["sources"]),
                   correct=correctness.label == "correct", correct_reason=correctness.reason)
    return row


def load_saved(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def print_row(r):
    labels = {"hit": ("hit", "MISS"), "correct": ("correct", "WRONG"),
              "abstained": ("abstained", "ANSWERED"), "faithful": ("faithful", "UNFAITHFUL")}
    flags = [labels[key][0 if r[key] else 1] for key in labels if key in r]
    print(f"{r['id']}  {r['type']:<12} {'  '.join(flags)}", flush=True)
    for key, reason in (("correct", "correct_reason"), ("abstained", "abstained_reason"), ("faithful", "faithful_reason")):
        if reason in r and not r[key]:
            print(f"     {key}: {r[reason]}", flush=True)


def format_summary(s):
    parts = [("hit", f"hit@{K}", ".3f"), ("rr", "MRR", ".3f"), ("correct", "correct", ".3f"),
             ("faithful", "faithful", ".3f"), ("abstained", "abstain", ".3f"),
             ("latency", "latency", ".2f"), ("tokens", "tokens", ".0f")]
    return "  ".join(f"{name} {s[key]:{fmt}}" for key, name, fmt in parts if s[key] is not None)


def report(rows):
    by_type = defaultdict(list)
    for r in rows:
        by_type[r["type"]].append(r)
    print()
    for type_name, group in sorted(by_type.items()):
        print(f"{type_name:<12} n={len(group):<3} {format_summary(summarize(group))}")
    print(f"{'ALL':<12} n={len(rows):<3} {format_summary(summarize(rows))}")


def main():
    parser = argparse.ArgumentParser(description="Run the golden set and report metrics.")
    parser.add_argument("case_id", nargs="?", help="run one question, without saving")
    parser.add_argument("--run", default="v0", help="name of the results file")
    parser.add_argument("--retrieval-only", action="store_true", help="hit@k and MRR only, no Gemini calls")
    args = parser.parse_args()
    questions = load_golden(args.case_id)

    if args.retrieval_only:
        rows = [score_retrieval(q) for q in questions if q["type"] != "unanswerable"]
        for r in rows:
            print_row(r)
    elif args.case_id:
        rows = [score_question(q) for q in questions]
        for r in rows:
            print_row(r)
    else:
        # Saved after every question, so a stopped run loses at most the question in progress.
        path = RESULTS / f"{args.run}.jsonl"
        rows = load_saved(path)
        done = {r["id"] for r in rows}
        if done:
            print(f"continuing {path.name}: {len(done)} questions already saved")
        RESULTS.mkdir(exist_ok=True)
        for q in questions:
            if q["id"] in done:
                continue
            r = score_question(q)
            with path.open("a") as f:
                f.write(json.dumps(r) + "\n")
            rows.append(r)
            print_row(r)

    if rows:
        report(rows)
    else:
        print("unanswerable question: not scored by retrieval metrics")


if __name__ == "__main__":
    main()
