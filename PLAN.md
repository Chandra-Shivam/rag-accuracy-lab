# RAG Accuracy Lab: one-week plan

**Goal:** build a naive "chat with your documents" RAG system, measure how wrong it is, then improve it one change at a time, recording the effect of every change. The deliverable is a working app **plus a before/after results table**: the evidence that clients asking to "fix our hallucinating chatbot" want to see.

**Stack:** Python 3.12 · LangChain / LangGraph · Pinecone (new) · Gemini (generation) · local sentence-transformers embeddings (bge-small-en-v1.5) · LangSmith · FastAPI · Docker

**Ground rules (carried over from MedInfo Agent)**

- Predict before you run. Write the prediction down, then compare.
- Change **one thing at a time**, and re-run the eval after each change.
- Every experiment gets a row in `EXPERIMENTS.md`, including the ones that made things worse.
- Commit after each working step. Never commit `.env`.
- Free-tier quotas are tight. Keep the first corpus to about 300 pages, cache embeddings to disk (keyed by embedding model + chunk text) so unchanged chunks are never re-embedded, and run single eval cases while debugging.
- Keep the embedding model fixed for every experiment. Changing it is an experiment in its own right, with its own index and its own `EXPERIMENTS.md` row.

---

## Day 1: Corpus and golden eval set

**Objective:** decide what "correct" means before writing any RAG code.

**Concepts:** golden datasets; answerable vs unanswerable questions; question types (single fact, multi-part, comparison, needs-a-table, not-in-the-docs); why an eval set must exist before the system.

**Tasks**
1. Corpus: 20–40 IRS publications and form instructions (US federal works, public domain), each the revision currently in effect for 2026 (anything explicitly for another tax year is excluded), about 300 pages in total. Include several with tables and multi-column layouts, because that's where naive RAG breaks.
   - Don't commit the PDFs: add `corpus/*.pdf` to `.gitignore`. Commit `corpus/SOURCES.md` (filename, URL, revision, page count, licence). A small download script rebuilds `corpus/` from it.
2. Write **40–60 eval questions** in `evals/golden.jsonl`. Each has: id, question, expected answer (short), type, and `gold`, a list of `{source, page}` locations. At least 20% must be **unanswerable** from the corpus.
   - `page` is the **1-based page index in the PDF file** (the file's first page = 1), **not** the number printed on the page.
   - List several gold pages only when **every** one is needed to answer; otherwise list the single most authoritative page.
   - Unanswerable questions have `"answer": null` and `"gold": []`.
   - Every answer must be verifiable on its cited gold page(s).
   `.jsonl` is **JSON Lines**: one complete JSON object per line, with no surrounding `[ ]` list. For example:
   ```
   {"id": "q01", "question": "What is the warranty period?", "answer": "2 years", "type": "single_fact", "gold": [{"source": "manual_a.pdf", "page": 14}]}
   {"id": "q02", "question": "Does the device support 5G?", "answer": null, "type": "unanswerable", "gold": []}
   ```
3. Write down your prediction: which question types will naive RAG get wrong most often?
4. Validate the file: every line parses; ids are unique; ≥20% unanswerable; every answerable question has ≥1 gold entry; every unanswerable one has `answer: null` and `gold: []`; every gold source is in SOURCES.md and every page is within that PDF's page count.

**Check:** can you explain why unanswerable questions are as important as answerable ones for a "hallucinating chatbot" client?

---

## Day 2: Naive baseline (v0)

**Objective:** build the simplest version, the kind most clients already have.

**Concepts:** PDF text extraction and its failure modes; fixed-size chunking; **Pinecone** (indexes, namespaces, metadata, upserts); top-k dense retrieval.

**Tasks**
1. Load PDFs page by page, keeping `source` and `page` metadata.
   - Page numbering: PyPDFLoader's `metadata["page"]` is 0-based. Convert to 1-based in exactly one place, the loader, so it matches the golden-set convention.
   - Always use `metadata["page"]`, never `metadata["page_label"]` (that's the printed page number).
   - Add a test that pins the convention: loading a known PDF must produce a minimum page of 1. (TODO(human): I write this test myself.)
2. Fixed-size chunks (e.g. 1,000 characters, no structure awareness), embed locally with `BAAI/bge-small-en-v1.5` (384-dim, normalized, cosine; queries get the bge instruction prefix, documents don't), upsert to a Pinecone index named for the model. Check that no chunk exceeds 512 tokens.
3. Retrieve top-k and generate an answer with a simple prompt. **No** grounding rules, citations or abstention yet. This is deliberately naive.
4. Expose it as one function, `answer(question) -> {answer, sources}`, so every later version is tested the same way.

**Check:** run five golden questions by hand. Which failed, and was the cause retrieval (wrong chunks) or generation (right chunks, wrong answer)?

---

## Day 3: Measure the baseline

**Objective:** turn "it seems a bit wrong" into numbers.

**Concepts:** **retrieval metrics** (hit rate@k: did the gold page appear in the top k? MRR: how high?) vs **generation metrics** (correctness, faithfulness to retrieved text, correct abstention on unanswerable questions); LLM-as-judge with calibration; LangSmith datasets and experiments.

**Tasks**
1. Write `evals/run.py` that runs the whole golden set and reports: hit rate@k, MRR, correctness, faithfulness, abstention accuracy, average latency and tokens per question.
   **Metric definitions (fixed on Day 1, before any results):**
   - hit@k: a question is a hit only if **all** of its gold pages appear in the top-k chunks.
   - MRR: 1 / rank of the first gold page found; 0 if none is found.
   - Unanswerable questions are excluded from hit@k and MRR; they're measured only by abstention accuracy.
2. Reuse the judge pattern from MedInfo: structured verdict, hand-labelled calibration examples, stability across runs.
3. Upload the golden set as a **LangSmith dataset** and run v0 as the first experiment.
4. **Error analysis:** label every failure with a cause (chunk split mid-answer, table lost, wrong document retrieved, answered when it should have abstained, …). Count them.

**Check:** which failure cause is most frequent? That decides what to fix first on Day 4. Record v0 as row 1 of `EXPERIMENTS.md`.

---

## Day 4: Improve retrieval, one change at a time

**Objective:** raise hit rate and MRR, and know exactly which change did it.

**Concepts:** structure-aware chunking (headings, pages, tables); chunk size and overlap trade-offs; metadata filtering; **hybrid search** (keyword/BM25 + dense); **re-ranking** (retrieve many, then re-score the top few); the cost and latency each adds.

**Tasks** (pick in the order your Day 3 error analysis suggests; re-run the eval after **each**):
1. Better chunking (structure-aware, tuned size/overlap).
2. Hybrid search.
3. Re-ranking.
4. Optional: query rewriting for vague questions.
5. Embedding swap: re-embed the same chunks with Gemini embeddings into a **separate Pinecone index** (different vector space; usually different dimension too). Same chunks, same k, same prompt, so the only change is the embedding model. Check first that the Pinecone free plan's index limit allows a second index.

**Check:** for each change, predict the effect on hit rate *before* running. Which change surprised you, and why?

---

## Day 5: Improve generation

**Objective:** stop hallucinations even when retrieval is imperfect.

**Concepts:** grounding prompts; mandatory citations (document and page); **abstention** ("the documents don't cover this") driven by retrieval scores plus the model's own judgement; code checks on the answer (cited sources must be among the retrieved chunks, as in MedInfo's `verify`).

**Tasks**
1. Add grounding rules and required citations; re-run.
2. Add abstention; watch both abstention accuracy **and** correctness (too eager to abstain is also a failure).
3. Add a code-level citation check; re-run.
4. Record cost and latency per version next to accuracy.

**Check:** build the final results table: v0 → each change → final, with every metric. Which single change gave the biggest improvement per extra second of latency?

---

## Day 6: Ship it

**Objective:** make it usable and demoable.

**Concepts:** streaming responses (FastAPI `StreamingResponse` or server-sent events); a minimal chat UI (Streamlit or a single HTML page); showing citations with page links; Docker; tracing in production.

**Tasks**
1. FastAPI `/ask` with streaming, returning citations.
2. A simple chat UI that shows the answer streaming and clickable sources.
3. Dockerfile (cache-friendly order, non-root, no secrets, version tag), run locally.

**Check:** demo end to end, including one unanswerable question that it correctly declines.

---

## Day 7: Case study and portfolio

**Objective:** turn the work into something that wins proposals.

**Tasks**
1. README: problem, architecture diagram, **results table**, what each change did, limitations, how to run.
   Include the disclaimer: "Reports what IRS publications say; not tax advice."
2. Two-minute demo video: one good answer with citations, one correct refusal, then the results table.
3. LinkedIn post focused on the lesson, not the stack.

**Check:** mock interview question: "Our RAG chatbot hallucinates. How would you fix it?" Answer using your own numbers.

---

## Next project (after this one)

**Agentic workflow with tools and approvals:** an agent that takes real actions through APIs (for example email triage or CRM updates), with human approval steps, retries and error handling. This fills the main gap from MedInfo Agent (no external tool calls).

---

## `EXPERIMENTS.md` template

| Version | Change | Hit@5 | MRR | Correct | Faithful | Abstain acc. | Latency (s) | Tokens/q | Notes |
|---|---|---|---|---|---|---|---|---|---|
| v0 | Naive baseline | | | | | | | | |
| v1 | | | | | | | | | |
