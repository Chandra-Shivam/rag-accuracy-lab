"""MEASURE box of MAP.md: log a saved run as a LangSmith experiment.

Usage: python evals/langsmith_experiment.py v0_run3
Reads evals/results/<run>.jsonl. Makes no Gemini calls. Each use creates a new experiment.
"""
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "evals" / "results"
DATASET_NAME = "irs-golden-v1"
SCORES = ("hit", "rr", "correct", "faithful", "abstained", "latency", "tokens")


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python evals/langsmith_experiment.py <run>")
    run_name = sys.argv[1]
    load_dotenv(ROOT / ".env")
    rows = [json.loads(line) for line in (RESULTS / f"{run_name}.jsonl").read_text().splitlines()]
    saved = {r["question"]: r for r in rows}

    def saved_answer(inputs):
        r = saved[inputs["question"]]
        return {"answer": r["answer"], "context": r["context"], "sources": r["sources"],
                "scores": {key: r[key] for key in SCORES if key in r}}

    def saved_scores(outputs):
        return {"results": [{"key": key, "score": float(value)} for key, value in outputs["scores"].items()]}

    results = Client().evaluate(saved_answer, data=DATASET_NAME, evaluators=[saved_scores],
                                experiment_prefix=run_name, description=f"Saved results from {run_name}")
    print(f"logged experiment: {results.experiment_name}")


if __name__ == "__main__":
    main()
