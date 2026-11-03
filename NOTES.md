# Notes

Quick reference for the flow, the files and answers to past doubts. Keep each entry to 1–2 lines.

## Flow (see MAP.md)

| Box | File / function | In → out |
|---|---|---|
| load pages | `rag/ingest.py` `load_pages()` | PDFs → one Document per page, metadata `source`, `page` (1-based) |
| chunk | `rag/ingest.py` `chunk_pages()` | pages → 1,000-char slices, metadata + `chunk_index`, id `source:page:index` |
| embed | `rag/embed.py` `CachedBgeEmbeddings` | text → 384-number vector (bge-small), cached on disk |
| store | `rag/store.py` `get_store()`, `upsert_chunks()` | chunks → vectors + metadata in Pinecone index `irs-bge-small-en-v1-5` |
| answer | `rag/answer.py` `answer()` | question → top-5 chunks → `gemini-3.5-flash-lite` (fixed sampling) → `{answer, sources}` (sources in rank order) |
| measure | `evals/` | golden set → metrics → EXPERIMENTS.md row |

## Files

- **STATUS.md**: what's done, where to resume, new-machine setup. **.claude/**: project settings.
- **corpus/SOURCES.md**: list of the 20 IRS PDFs (URL, revision, page count). PDFs aren't in git.
- **corpus/download.py**: rebuilds `corpus/` from SOURCES.md and warns if a page count changed.
- **evals/golden.jsonl**: the exam: question, correct answer, type, gold pages.
- **evals/golden_evidence.jsonl**: the proof: an exact quote from each gold page; `absent` words for unanswerable questions.
- **evals/validate_golden.py**: checks the format of golden.jsonl, and that each quote really is on its gold page.
- **evals/metrics.py**: `is_hit()`, `reciprocal_rank()` and `summarize()`, pure functions pinned by **tests/test_metrics.py**.
- **evals/run.py**: runs the golden set through `answer()` and the judges, saves each question to `evals/results/<run>.jsonl`, continues a stopped run, prints metrics per type and overall. `--retrieval-only` needs no Gemini.
- **evals/judge.py**: `judge_correctness()` and `judge_faithfulness()` return structured verdicts. `python -m evals.judge correctness|faithfulness` checks one against its hand labels, 3 runs each. `prepare-faithfulness` creates the examples.
- **evals/judge_calibration.jsonl**: 10 real v0 answers with hand labels (correctness).
- **evals/abstention_calibration.jsonl**: saved v0 answers with hand labels (abstained/answered).
- **evals/faithfulness_calibration.jsonl**: real v0 answers + their context + hand labels (faithfulness), created by `prepare-faithfulness`.
- **pytest.ini**: puts the project root on the import path so plain `pytest` finds `rag` and `evals`.
- **rag/ingest.py**: `load_pages()` loads and converts page numbers (+1, the only place this happens); `chunk_pages()` slices pages into chunks.
- **rag/embed.py**: `embed_documents()` embeds only texts that aren't in the cache; `embed_query()` adds the bge prefix and isn't cached.
- **rag/store.py**: creates the Pinecone index if missing (384 dims, cosine, free plan = AWS us-east-1) and upserts chunks by fixed id. Key comes from `.env`.
- **rag/answer.py**: `retrieve(question)` does top-k search only (no LLM). `answer(question)` calls it, sends a naive prompt to Gemini, returns the answer and the retrieved pages. Same function for every version.
- **tests/test_ingest.py**: pins the 1-based page rule on `tests/fixtures/fw4s.pdf` (2 pages).
- **data/cache/embeddings/**: cached vectors (JSONL, git-ignored, can be rebuilt).

## Rules we fixed on Day 1

- **page** = 1-based page index in the PDF file. Not the printed number, never `page_label`. PyPDFLoader starts at 0, hence the +1.
- **gold page** = the page where the answer is written. Unanswerable questions have `answer: null`, `gold: []`.
- **hit@k** = were **all** gold pages in the top-k chunks? Unanswerable questions are skipped (they're measured by abstention).
- **MRR** = 1 / rank of the first gold page found (0 if none).
- One change per experiment; the embedding model stays fixed (changing it is its own experiment, with its own index).

## Doubts and answers

- **Fixed vs recursive chunking?** Fixed cuts every N chars (even mid-word). Recursive prefers paragraph → line → word breaks. Overlap is a separate setting that works with either.
- **Is chunking page-wise by default?** Our choice: PyPDFLoader `mode="page"`. `mode="single"` allows chunks across pages, but loses clean page numbers.
- **Why 1,714 chunks, not 942?** Average page ≈ 5,000 chars, not 2,500, and each page's last partial chunk rounds up.
- **Why each metadata field?** `text` gets sent to the LLM and is read when debugging; `chunk_index` finds neighbouring chunks; a fixed id means re-upserting overwrites instead of duplicating.
- **Off-by-one in pages?** Every retrieval scores as a miss, and wrong pages can be scored as hits. Hence the test.
- **A test that has never failed?** It proves nothing. Break the code on purpose and check the test catches it.
- **Is PyTorch used?** Not directly. sentence-transformers runs on it (like EF Core on ADO.NET). It makes the Docker image big.
- **Why the cache?** It saves time and API quota on re-runs. The key includes the model name, so vectors from different models never mix. It only helps if the chunk text is unchanged.
- **How are duplicates found?** Cache hits on an empty cache meant identical texts. Pub 15 p58 = Pub 15-A p27 (boilerplate).
- **Re-indexing in production?** Track a content hash per chunk; re-embed only changed chunks; delete removed ones (LangChain Indexing API). The vector DB is the main store.
- **Why Pinecone, not Chroma?** At our scale Chroma would work just as well. Pinecone is managed (no ops, easy Docker deploy, namespaces, metadata filters) and is a common choice for clients. The DB choice affects latency and ops, barely accuracy.
- **When are chunks embedded in store.py?** Not in `get_store()` (that only builds the embedder). `add_documents()` calls our `embed_documents()` in batches, then upserts. Queries call `embed_query()` inside `similarity_search()`.
- **Chunk vs token?** Chunk = the 1,000-char piece we cut (one vector, one Pinecone record). Token = the word-sized piece the model splits a chunk into (~231 per chunk).
- **Why do 1,000 chars give 230 or 680 tokens?** Common words = 1 token (~6 chars); every `.` `,` and number piece is its own token (~1.5 chars). Dotted tables are token-heavy. Size chunks in tokens.
- **How to check the 512-token limit?** Count with the model's own tokenizer (`AutoTokenizer.from_pretrained(MODEL)`), not characters. Median chunk = 231 tokens, but 57 chunks are over 512 (max 681): dotted table rows like `8,000 to 8,999 ..... 2,600`. bge silently cuts off the rest.
- **Day 2 hand check (5 questions):** q15 got the right pages but the wrong chunk (answer in p15t `7:0`, retrieved `7:1`), so page-level hit@k can be a false hit. q01 missed its gold page but answered correctly from fw4 p3. q39 hallucinated instead of abstaining.
- **Why does re-running store.py not duplicate?** Upsert = insert or overwrite by id. Fixed ids → 2 runs still give 1,714 vectors. Random ids would give 3,428 (duplicates in top-k).
- **Where are embeddings stored?** Only in the cache file for now; the return value lives in memory. Pinecone will be the permanent store. Query vectors aren't stored.
- **Golden set from an LLM?** Fine if each answer has a page quote checked in code, unanswerable questions are proven absent, and a human spot-checks some.
- **What the validator can't check:** whether a quote actually *supports* the answer (only that the quote exists). That's what the human spot-check is for.
- **Near-miss?** An unanswerable question with lookalike content in the corpus (e.g. employer penalties for an individual penalty question). It tempts the model into answering.
- **Unanswerable vs underspecified?** Unanswerable: the documents don't contain it, so abstain. Underspecified: the user didn't give enough, so ask a clarifying question.
- **Why unanswerable questions at all?** Hallucination means answering when you shouldn't; only these questions measure that.
- **MRR full form?** Mean Reciprocal Rank: per question 1 / rank of the first gold page (rank 1 → 1.0, rank 3 → 0.33, miss → 0), then average over questions.
- **Why retrieval metrics first on Day 3?** They need no LLM, so no quota and no judge. If the right page isn't retrieved, the model can't answer from it, so this separates retrieval failures from generation failures.
- **Why tests/test_metrics.py?** A buggy metric still prints a believable number, and every experiment is compared on it. The test feeds small made-up inputs with known answers (no Pinecone) and fails if the definition breaks.
- **What is pytest?** Python's standard test runner (like `dotnet test` with xUnit): it finds `test_*` functions in `tests/`, runs them, reports pass/fail. It doesn't cover `answer()`, so that was checked with one real Gemini call after the refactor.
- **Why `<=` in `is_hit()`?** On Python sets, `<=` means "is a subset of": every gold page must be among the retrieved pages. It isn't a numeric comparison.
- **Functions in evals/judge.py?** `Verdict` = the required reply shape; `_get_judge()` builds the Gemini client once; `judge_correctness()` grades one answer; `calibrate()` compares the judge with hand labels over 3 runs.
- **What is a necessary detail for the judge?** Only what the question asks for. Other details in the golden answer are optional (q31: default rates asked, so the 0-100% choice is optional).
- **Correctness vs faithfulness?** Correctness compares the answer with the golden answer. Faithfulness compares it with the chunks that generated it, with no golden answer and no new DB query, so `answer()` must also return its context.
- **Calibrating vs using a judge?** Calibrating tests the judge on a small hand-labelled file. Using it scores the system on the golden set. Each judge needs its own calibration file. Faithfulness only needs an answer + its chunks, so it can also run in production.
- **What does `prepare_faithfulness()` do?** Takes the 8 questions in `FAITHFULNESS_IDS` from golden.jsonl, runs each through `answer()`, and saves question + context + answer with an empty label. The judge doesn't generate answers; it only grades them.
- **Temperature warning from Gemini?** `gemini-3.5-flash-lite` uses fixed sampling and ignores `temperature`, so we removed the setting. Answers may vary between runs; measure that noise before trusting small metric changes.
- **Eval noise floor?** How much a score moves when nothing changed. Run the same version twice or more and compare each metric with itself (Correct vs Correct, Faithful vs Faithful), never Correct vs Faithful. A later change smaller than that movement isn't proven to be an improvement.
- **Is "the context doesn't say" faithful?** Yes, if that is true: faithfulness only asks whether the answer describes the chunks truthfully. It can still fail correctness (q36).
- **Judge disagrees with a hand label?** Don't assume either is right; check the answer against the context. In the first faithfulness run the judge looked right on q39 and q41, and too lenient on q27.
- **Abstention, latency, tokens?** Abstention = declining when the documents don't have the answer; measured on unanswerable questions. Latency = seconds per question. Tokens = LLM usage, which drives cost. Accuracy alone can't show whether a change is worth its cost and delay.
- **How do you stop a RAG system making things up?** Layers: better retrieval, grounding prompt, citations, abstention, code checks on citations, and evals to measure it. No layer removes it fully, so measure and reduce it.
- **How many LLM judges in production?** No fixed number. Usually 0-1 blocking the reply, 1-3 running in the background on a sample, and the full set offline on the golden set before release. Each judge adds roughly one LLM call per item it checks.
- **What does the abstention judge see and decide?** It sees the question and reply, not the context, and decides whether the reply did decline. Whether it should have declined comes from the golden set (`type: unanswerable`).
- **How are judges run in production?** Usually one judge per metric. Offline: all of them on a golden set before release. Live: code checks first, then a cheap judge on a sample in the background, with humans reviewing flagged cases. Live traffic has no golden answers, so correctness stays mostly offline.
- **Do the judges need the golden.jsonl path?** No. `judge_*()` functions take text, not files. `calibrate()` reads calibration files; `evals/run.py` reads golden.jsonl and calls the same functions.
- **What does latency measure?** Retrieval + Gemini answer only. Judges, one-time loading and the wait for free-tier quota are excluded, since users wouldn't wait for those. So real latency under load may differ.
- **`expected` and `correct` in results?** `expected` is the golden answer from golden.jsonl, written on Day 1. `correct` is true when the correctness judge says the system's `answer` matches it. Unanswerable rows have `expected: null` and no `correct`.
- **v0 run 1 findings:** all 8 wrong answers trace back to retrieval (6 misses, 2 page-level false hits), so retrieval looks like the first thing to fix. q44's unanswerable label looks wrong: the corpus says digital assets are not accepted.
- **How are the per-type numbers calculated?** `summarize()` averages over that type's rows, using only the rows that have the metric. Each true counts as 1 and each false as 0, so comparison Correct 0.750 = 6 of 8.
- **Who decides "unanswerable"?** We do, in golden.jsonl, before any run. The judge only says whether the reply declined. Abstain acc. combines the two.
- **Failure stages:** ingestion (bad text/tables), retrieval (gold page not in top-k), generation (wrong answer or no abstention). Label every failure by stage.
- **v0 noise check:** equal totals can hide flips. Correct stayed 0.795, but q02 and q30 swapped. Compare runs per question: Correct noise is about 5 points, Faithful about 8. Retrieval is repeatable, so it has no run-to-run noise. Fix plan: hand-check the flips, then re-run the judge on saved answers to see whether the judge or the answer is causing them. Review copy of the 6 flips: `data/cache/flip_review.md` (git-ignored).
- **`evals/stability.py`:** judges the 6 flipped questions' saved answers 3 times each (36 calls). The answer text is fixed, so a changed verdict is judge noise.
- **Stability result:** 9/12 stable. Correctness 4/4, faithfulness 5/8, so faithfulness is the noisier judge. Stable does not mean right.
- **Correctness rule 4:** numbers and dates must be exact, including the year when the expected answer gives one. Two "year optional" wordings failed on q02, so q02 counts as wrong unless the answer gives 2026. Check it again on Day 4.
- **`evals/compare.py`:** `python evals/compare.py v0 v0_run2` compares two saved runs and lists each question that flipped. No Gemini calls.
- **What is `metric` in compare.py?** Just a key name, such as `"correct"`, used to read a saved value. `score_question()` in `evals/run.py` works out the per-question values; `compare.py` only reads them.
- **v0 baseline:** `evals/results/v0_run3.jsonl` (Correct 0.769, Faithful 0.880). q37 had the right numbers and the wrong conclusion, so generation can also fail when retrieval is right.
- **v0 error analysis:** of 9 wrong answers, 4 are near-miss retrieval (gold chunk at rank 6 to 20), 2 deep misses, 2 table chunks not retrieved, 1 generation. Near misses suggest trying re-ranking first on Day 4.
- **Who ranks chunks?** Not the LLM. Embeddings and Pinecone rank them by vector similarity, and the LLM only sees the final top 5. Re-ranking fetches many chunks, re-scores them, and still sends 5 to the LLM.
- **LangSmith 403:** a new API key fixed it. The old key failed on read and write, so the problem was the key, not the tracing code.
- **Dataset upload: script or UI?** The UI also works. A script is repeatable, keeps the steps in git, and maps fields the same way each time.
- **LangSmith scripts:** `evals/langsmith_upload.py` uploads the golden set as dataset `irs-golden-v1`. `evals/langsmith_experiment.py <run>` logs a saved run as an experiment, with no Gemini calls. If a score is missing from the UI, check the column settings; the API showed all 7 were stored.
- **Gemini free-tier limits:** 15 requests per minute and 500 per day per model. A full eval is about 150 calls.
- **q30 golden fix:** the answer now lists all three fax cases from iss4.pdf p2. The old one left out 855-641-6935.
