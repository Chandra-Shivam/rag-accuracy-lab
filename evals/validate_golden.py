"""Validate evals/golden.jsonl against the schema rules in PLAN.md (Day 1, task 4)
and against the corpus text.

Checks:
  - every line parses; ids unique; 40-60 rows; >=20% unanswerable
  - answerable: >=1 gold entry; unanswerable: answer null and gold []
  - every gold source is in corpus/SOURCES.md and every page is within 1..page count
  - every evidence quote is found on its gold page (pages are 1-based file indexes)
  - every "absent" term of an unanswerable question appears nowhere in the corpus
Also reports answerable questions whose evidence appears on pages outside their gold
list; with all-gold-pages hit@k, those can be scored as misses for a valid retrieval.

Usage: python evals/validate_golden.py
"""
import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "evals" / "golden.jsonl"
EVIDENCE = ROOT / "evals" / "golden_evidence.jsonl"
CORPUS = ROOT / "corpus"
TYPES = {"single_fact", "needs_table", "multi_part", "comparison", "unanswerable"}


def norm(text):
    # PDF text breaks words with spaces and hyphens ("W -4", "re- mains"); compare letters and digits only.
    return re.sub(r"[^a-z0-9$%]", "", text.lower())


def load_jsonl(path, errors):
    rows = []
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            errors.append(f"{path.name}:{n}: invalid JSON ({e})")
    return rows


def load_corpus():
    sources = {}
    for line in (CORPUS / "SOURCES.md").read_text().splitlines():
        if m := re.match(r"^\| (\S+\.pdf) \|.*?\| (\d+) \| [^|]+ \| [^|]+ \|$", line):
            sources[m.group(1)] = int(m.group(2))
    pages = {}
    for name in sources:
        reader = PdfReader(CORPUS / name)
        for i, page in enumerate(reader.pages, 1):
            pages[(name, i)] = norm(page.extract_text() or "")
    return sources, pages


def main():
    errors, warnings = [], []
    golden = load_jsonl(GOLDEN, errors)
    evidence = {row["id"]: row for row in load_jsonl(EVIDENCE, errors)}
    sources, pages = load_corpus()

    ids = [q.get("id") for q in golden]
    if len(ids) != len(set(ids)):
        errors.append(f"duplicate ids: {sorted({i for i in ids if ids.count(i) > 1})}")
    if not 40 <= len(golden) <= 60:
        errors.append(f"{len(golden)} questions; need 40-60")
    unanswerable = [q for q in golden if q.get("type") == "unanswerable"]
    if len(unanswerable) < 0.2 * len(golden):
        errors.append(f"only {len(unanswerable)}/{len(golden)} unanswerable; need >=20%")

    for q in golden:
        qid = q.get("id")
        if set(q) != {"id", "question", "answer", "type", "gold"}:
            errors.append(f"{qid}: fields {sorted(q)}")
            continue
        if q["type"] not in TYPES:
            errors.append(f"{qid}: unknown type {q['type']!r}")
        ev = evidence.get(qid, {})

        if q["type"] == "unanswerable":
            if q["answer"] is not None or q["gold"] != []:
                errors.append(f"{qid}: unanswerable needs answer null and gold []")
            if not ev.get("absent"):
                errors.append(f"{qid}: no absent terms to check")
            for term in ev.get("absent", []):
                found = [f"{s}:{p}" for (s, p), text in pages.items() if norm(term) in text]
                if found:
                    errors.append(f"{qid}: absent term {term!r} found on {', '.join(found[:5])}")
            continue

        if not isinstance(q["answer"], str) or not q["answer"].strip():
            errors.append(f"{qid}: answerable question needs a non-empty answer")
        if not q["gold"]:
            errors.append(f"{qid}: answerable question needs >=1 gold entry")
        gold = {(g.get("source"), g.get("page")) for g in q["gold"]}
        for source, page in gold:
            if source not in sources:
                errors.append(f"{qid}: source {source!r} not in SOURCES.md")
            elif not isinstance(page, int) or not 1 <= page <= sources[source]:
                errors.append(f"{qid}: {source} page {page} outside 1..{sources[source]}")

        quotes = ev.get("evidence", [])
        if not quotes:
            errors.append(f"{qid}: no evidence quotes")
        for e in quotes:
            key, quote = (e["source"], e["page"]), norm(e["quote"])
            if key not in gold:
                errors.append(f"{qid}: evidence page {key} is not a gold page")
            elif quote not in pages.get(key, ""):
                errors.append(f"{qid}: quote not found on {key[0]}:{key[1]}: {e['quote'][:60]!r}")
            elsewhere = [f"{s}:{p}" for (s, p), text in pages.items() if (s, p) not in gold and quote in text]
            if elsewhere:
                warnings.append(f"{qid}: evidence also on {', '.join(elsewhere[:5])}")

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    counts = {t: sum(q.get("type") == t for q in golden) for t in sorted(TYPES)}
    print(f"\n{len(golden)} questions {counts}; {len(errors)} errors, {len(warnings)} warnings")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
