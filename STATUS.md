# Status

Where the project is and where to resume. Update at the end of every session.

## Done
- **Day 1:** IRS payroll corpus (20 PDFs, 314 pages, `corpus/SOURCES.md`), 50-question golden set with page-quote evidence, validator passes (0 errors; known warnings for evidence that also appears on other pages). Predictions logged in EXPERIMENTS.md.
- **Day 2 (baseline v0):** `load_pages` → `chunk_pages` (1,000 chars, no overlap, 1,714 chunks) → bge-small embeddings (disk cache) → Pinecone index `irs-bge-small-en-v1-5` (1,714 vectors, already populated) → `answer(question)` with `gemini-3.5-flash-lite`, k=5, naive prompt.
- **Day 2 hand check** (q01, q15, q24, q31, q39): results in NOTES.md. Key findings: page-level hit@k can be a false hit (q15 wrong chunk on the right page); q39 hallucinated instead of abstaining; 57 chunks are over bge's 512-token limit (dotted tables).

## Resume here
**Day 3 in progress:** v0 retrieval is measured: hit@5 0.789, MRR 0.607 (EXPERIMENTS.md). Correctness judge calibrated: 10/10 agreement and stability on hand labels (same examples used to discuss the rules). Faithfulness judge written, not run yet (one verdict per answer: supported/not_supported). Faithfulness judge accepted with a known limitation (see EXPERIMENTS.md). Abstention judge calibrated: 8/8 agreement, 8/8 stable. Full v0 run 1 is saved in `evals/results/v0.jsonl` (see EXPERIMENTS.md). q44 was moved to answerable and re-scored. Run 2 for noise is done (`evals/results/v0_run2.jsonl`, noise check in EXPERIMENTS.md): retrieval did not move, Correct had 2 flips (q02, q30), Faithful had 4 (q12, q27, q32, q36), Abstain had 0. Correctness rule 4 was changed so a year may be left out if the question makes it clear; the saved runs used the old rule. q30's golden answer was fixed to add the 855-641-6935 case. Stability test done: 9/12 stable, and rule 4 is still applied inconsistently on q02 (see EXPERIMENTS.md). Rule 4 is final: dates must be exact, including the year when the expected answer gives one, so q02 counts as wrong unless it gives 2026 (check again on Day 4). The daily Gemini quota (500 requests per model) ran out during the correctness calibration re-check. Next: write `evals/compare.py` (no quota needed); after the quota resets, re-run `python -m evals.judge correctness` (30 calls), then run `python evals/run.py --run v0_run3` under the final rules as the new baseline, hand-check a sample of `supported` verdicts, label every failure's cause, then fix the LangSmith 403 and upload the dataset.
## Known follow-ups
- Day 4 candidates: chunks over 512 tokens, proof-mark junk on page 1, duplicate boilerplate chunks, recursive splitter and overlap (separate experiments).
- Before the Gemini embedding experiment: make the embedding cache save per batch.
- Before Day 6: migrate off the deprecated `langchain-community` PyPDFLoader.

## New machine setup
1. `python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt` (no python3.12: `uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt`)
2. `.venv/bin/python corpus/download.py` (PDFs aren't in git)
3. Create `.env` with `PINECONE_API_KEY` and `GOOGLE_API_KEY` (never commit it, never paste keys in chat)
4. `.venv/bin/python -m rag.embed` rebuilds the local embedding cache (~10 s). The Pinecone index is already populated; don't re-run `rag.store` unless the chunks change.
5. Check: `.venv/bin/pytest` passes.
