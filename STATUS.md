# Status

Where the project is and where to resume. Update at the end of every session.

## Done
- **Day 1:** IRS payroll corpus (20 PDFs, 314 pages, `corpus/SOURCES.md`), 50-question golden set with page-quote evidence, validator passes (0 errors, 5 known warnings). Predictions logged in EXPERIMENTS.md.
- **Day 2 (baseline v0):** `load_pages` → `chunk_pages` (1,000 chars, no overlap, 1,714 chunks) → bge-small embeddings (disk cache) → Pinecone index `irs-bge-small-en-v1-5` (1,714 vectors, already populated) → `answer(question)` with `gemini-3.5-flash-lite`, k=5, naive prompt.
- **Day 2 hand check** (q01, q15, q24, q31, q39): results in NOTES.md. Key findings: page-level hit@k can be a false hit (q15 wrong chunk on the right page); q39 hallucinated instead of abstaining; 57 chunks are over bge's 512-token limit (dotted tables).

## Resume here
**Day 3 in progress:** v0 retrieval is measured: hit@5 0.789, MRR 0.607 (EXPERIMENTS.md). Next: add generation metrics (see PLAN.md Day 3) and leave the real design decisions (how correctness and faithfulness are judged) to the user as TODO(human). Ask for a prediction before the full 50-question run. Then latency and tokens, LangSmith dataset, and error analysis including the 8 retrieval misses.

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
