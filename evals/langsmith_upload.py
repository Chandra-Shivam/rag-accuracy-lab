"""MEASURE box of MAP.md: upload the golden set as a LangSmith dataset.

Usage: python evals/langsmith_upload.py
Needs LANGSMITH_API_KEY in .env. Makes no Gemini calls.
"""
import json
import sys
from pathlib import Path

from dotenv import load_dotenv
from langsmith import Client

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "evals" / "golden.jsonl"
DATASET_NAME = "irs-golden-v1"


def to_example(q):
    return {
        "inputs": {"question": q["question"]},
        "outputs": {"answer": q["answer"]},
        "metadata": {"id": q["id"], "type": q["type"], "gold": q["gold"]},
    }


def main():
    load_dotenv(ROOT / ".env")
    client = Client()
    if client.has_dataset(dataset_name=DATASET_NAME):
        sys.exit(f"{DATASET_NAME} already exists; not uploading again")

    questions = [json.loads(line) for line in GOLDEN.read_text().splitlines() if line.strip()]
    dataset = client.create_dataset(DATASET_NAME, description="IRS payroll golden set, 50 questions")
    client.create_examples(dataset_id=dataset.id, examples=[to_example(q) for q in questions])
    print(f"uploaded {len(questions)} examples to {DATASET_NAME}")


if __name__ == "__main__":
    main()
