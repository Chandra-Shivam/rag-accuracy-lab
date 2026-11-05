"""MEASURE box of MAP.md: run the citation check on a saved run.

Usage: python evals/check_citations.py v6_prompt_fixes
Reads evals/results/<run>.jsonl. Makes no Gemini calls. Exact refusals are left out, as they make no claim.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# "python evals/check_citations.py" puts evals/ on the path, not the project root.
sys.path.insert(0, str(ROOT))

from rag.answer import is_refusal
from rag.citations import check_citations, citations_ok


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python evals/check_citations.py <run>")
    path = ROOT / "evals" / "results" / f"{sys.argv[1]}.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    answers = [r for r in rows if not is_refusal(r["answer"])]
    results = {r["id"]: check_citations(r["answer"], r["context"]) for r in answers}

    print(f"answers checked {len(answers)}  ok {sum(map(citations_ok, results.values()))}")
    print(f"citations valid {sum(len(c['valid']) for c in results.values())}"
          f"  invalid {sum(len(c['invalid']) for c in results.values())}")
    for qid, result in results.items():
        if not citations_ok(result):
            print(f"  {qid}  invalid {result['invalid']}" if result["invalid"] else f"  {qid}  no citations")


if __name__ == "__main__":
    main()
