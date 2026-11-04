# Notes

Quick reference for the flow, the files and answers to past doubts. Keep each entry to 1–2 lines.

## Flow (see MAP.md)

| Box | File / function | In → out |
|---|---|---|
| load pages | `rag/ingest.py` `load_pages()` | PDFs → one Document per page, metadata `source`, `page` (1-based) |
| chunk | `rag/ingest.py` `chunk_pages()` | pages → 1,000-char slices, metadata + `chunk_index`, id `source:page:index` |
| embed | `rag/embed.py` `CachedBgeEmbeddings` | text → 384-number vector (bge-small), cached on disk |
| store | `rag/store.py` `get_store()`, `upsert_chunks()` | chunks → vectors + metadata in Pinecone index `irs-bge-small-en-v1-5` |
| answer | `rag/answer.py` `answer()` | question → vector top 20 + BM25 top 20 → RRF, up to 40 candidates → re-rank to top 5 → add neighbouring chunks → `gemini-3.5-flash-lite` (fixed sampling) → `{answer, sources}` (sources = top 5 in rank order) |
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
- **data/cache/embeddings/**: cached vectors (JSONL, git-ignored, can be rebuilt). Not on this machine yet; `embed_documents()` creates it, and evals don't need it because search uses Pinecone.

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
- **Where are embeddings stored?** Created locally by bge, saved in the disk cache (to skip repeat work) and in Pinecone (the store that search uses). Query vectors are created locally for each question and aren't stored.
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
- **`rag/rerank.py`:** re-scores Pinecone's top chunks with a local cross-encoder and keeps the best k. `score_pairs` is an optional scorer so tests can skip the model. `run.py --retrieval-only --candidates N` tests it without Gemini; 0 turns it off.
- **v1 re-ranking:** Hit@5 0.795 to 0.897, Correct 0.769 to 0.846. It can also hurt: q24 lost the chunk with the 6.0% rate. Most of the latency rise was Gemini time, not the re-ranker.
- **Real regression vs noise?** Regression = a question gets worse after a change. Call it real when a repeatable cause explains it: q24 was right in all 3 v0 runs, then re-ranking removed the "6.0" text from its context. Hit@5 stayed true, so only the per-question check showed it.
- **v1 run 2:** same contexts, Correct 0.872, Abstain 0.818. q24 is a judge false pass (the answer still lacks 6.0%) and q40 looks like judge noise, so read the answer before trusting a flip. Median latency fell back to 1.97 s, so re-ranking didn't cause run 1's jump.
- **How do you know an eval can be trusted?** Check each layer: golden set (quotes verified), metric code (unit tests), judges (hand labels, repeat for stability), noise floor (repeat runs), flips (read the answers). It lowers the risk but doesn't prove the eval is right.
- **Chunk check for q15, q35, q24:** the Table 2 chunk (p15t `7:0`, 416 tokens) starts with PDF header junk and isn't cut off by the 512 limit. q24's 6.0% sits at the end of p15 `44:1`, with the credit in `44:2`. Only 7 of the 57 over-limit chunks matched a dotted-row pattern, so the earlier "dotted tables" note may be too broad.
- **Recursive splitter preview:** our PDF text has no blank lines (0 of 314 pages), so it can't cut at paragraphs, only at line ends. 1,746 chunks, and q24's and Table 2's chunks look almost unchanged, so it may not fix q15, q35 or q24.
- **Chunking A result:** Hit@5 0.897, MRR 0.716, so no gain over v1. q22 and q44 fixed, q34 and q36 lost. Table 2 is still too far down the vector search, and the re-ranker puts q24's 6.0% chunk at rank 9.
- **PDF header junk:** 277 of 314 pages start with about 200 chars of proof text ("Page 7 of 71 Fileid..." and "MUST be removed before printing"), so it takes about 20% of each page's first chunk. Junk cleanup (B) would remove it.
- **Chunking B result:** Hit@5 0.821, MRR 0.635, worse than v1. q24's 6.0% came back, but q01, q17 and q34 became misses and Table 2 fell out of the top 50. A sensible-looking cleanup can still lower the score, so measure it.
- **Neighbouring chunks (small-to-big)?** Search with small chunks, then also send the chunks next to each match to the LLM. Fixed ids (`p15t.pdf:7:1` = file, page 7, chunk 1) let us fetch neighbours from Pinecone with no re-indexing. It could bring in Table 2 (`7:0`) because `7:1` is already retrieved; not tested yet. Hit@5 reads only `sources`, so if neighbours stay out of `sources` it can't change; same-page neighbours add no new pages, so measure them by checking the evidence text in the context. The sketch stops at page edges, so neighbours on other pages need extra code.
- **Neighbours vs parent page (local check on v1's top 5):** median context is about 1,150 bge tokens for top 5, 2,800 with neighbours and 6,100 with whole pages. Both bring in Table 2 and q24's 6.0%. Whole pages cost about twice the tokens of neighbours.
- **When does `rag/neighbours.py` run?** At question time, inside `retrieve()`, after `rerank()` and before the context is built. Not during indexing.
- **`rag/neighbours.py`:** `neighbour_ids()` works out the ids to fetch and `join_chunks()` joins them in reading order, with no separator between next-door chunks because fixed cuts can split a word. `WINDOW` in `rag/answer.py` sets the size; 0 turns it off.
- **`evidence_found()` in `evals/metrics.py`:** true if all of a question's gold quotes are in the context, from any page. Hit@5 checks pages, so it can't see missing text. An answer can still be right from another page (q20), so it isn't the same as Correct.
- **Parent document and window size?** Parent document: search small child chunks, then send the bigger parent each one belongs to (for us, the page). Window size: how many chunks to add on each side of a match, so window 1 gives up to 3 chunks per match and window 2 up to 5.
- **Where is the parent stored?** Outside the vector search, in a separate store (Postgres, Redis, blob storage), found by `parent_id`. It has no vector. We have no such store; our page could be rebuilt by joining its no-overlap chunks from Pinecone.
- **v2 neighbouring chunks:** Correct 33/39 by hand to 36/39, Faithful 1.000, tokens about 2.3 times higher. q15, q35 and q24 are fixed. Still wrong: q02 (generation), q08 and q22 (retrieval).
- **Pinecone indexes:** `irs-bge-small-en-v1-5` (default) and `irs-gemini-embedding-2`, 1,714 vectors each. The recursive and cleaned indexes were deleted. Recursive's code was never committed, so testing it again means rewriting it; `CLEAN=before` or `CLEAN=after` with `python -m rag.store` rebuilds a cleaned index. Results stay in EXPERIMENTS.md.
- **Hybrid search?** Run vector search (meaning) and keyword search (BM25, exact words), then merge the two lists, usually with Reciprocal Rank Fusion. It may help q08 ("W-4S"), but q22's gold chunk is already in the top 20, so the re-ranker is its blocker. Not tested yet.
- **How does RRF work?** Each chunk scores `1 / (60 + rank)` per list it appears in, and the scores are added, so chunks in both lists rise. 60 is the original paper's value and a common default; it keeps rank 1 from dominating. The fused top 20 then go to the re-ranker.
- **`rag/hybrid.py`:** `keyword_search()` runs BM25 over chunks rebuilt from the PDFs (about 9 s once per process, 2 ms per search) and `fuse()` applies RRF. `HYBRID_N` in `rag/answer.py` sets the chunks taken from each search; `--hybrid 0` gives vector only. The API now needs the PDFs at run time.
- **How does BM25 score?** Each question word found in a chunk adds to its score; not all words have to match. Rare words add more, repeats add less each time, and long chunks count slightly less. Our tokenizer has no stemming, so "employee" doesn't match "employees".
- **Is BM25 stored in Pinecone? Why PDFs?** No, it stays in memory on our machine as word counts per chunk, with no re-indexing or vectors. It needs the text of every chunk, and the PDFs were the easiest source; a saved chunk file would also work and would remove the PDF need.
- **What is a tokenizer?** It splits text into the pieces a system works on. We have two: `tokenize()` in `rag/hybrid.py` for BM25 (our own rule, used on both chunks and question), and bge's for embeddings (comes with the model; sentence-transformers runs it, we didn't write it). Their tokens are different.
- **Hybrid retrieval-only result:** N = 20 gives Hit@5 0.949, MRR 0.742, Evidence 36/39. q08 is fixed, q22 is a page-level false hit, and q36 is lost because fusion cuts its chunks before re-ranking. A chunk in one list only can lose to chunks in both, even at a good rank.
- **Why can a bigger N lose chunks?** Fusion always keeps 20. Below N = 62, a chunk in both lists always outscores a chunk in one list (2/(60+N) > 1/61), and longer lists put more chunks in both. q20: 7 in both at N = 20, 24 at N = 50, so its BM25-only chunk was cut.
- **Hybrid without the cut:** N = 20 with 40 candidates gives Hit@5 0.974, MRR 0.776, Evidence 37/39, and q36 is back, for about 0.1 s more retrieval time. q22 is still a false hit. Chosen on the same 39 questions, so possibly a little optimistic.
- **v3 hybrid search:** Correct 36/39 from the judge, 37/39 by hand (q31 is a judge false fail, re-judged correct 3 of 3). q08 is fixed; q02 and q22 are still wrong. Median latency rose to 19.95 s, but a new Gemini key changed in the same run, so the cause isn't confirmed.
- **q31 vs q39 in v3:** q31 is a judge error: the answer is right, but the correctness judge failed it. q39 is a real failure: the system should have declined, and the abstention judge correctly says it answered.
- **v3 run 2:** Correct 37/39, Faithful 50/50, Abstain 10/11. q31 flipped to correct, supporting the judge-error reading. Median latency fell from 19.95 s to 2.39 s with the same retrieval code, so hybrid search didn't cause the jump. Gemini is 65% of total time.
- **What is one run?** Each of the 50 questions once: 1 answer call + 2 judge calls per question, about 150 Gemini calls. The 3 is calls per question, not repeats. Full runs so far: v0 3, v1 2, v2 1, v3 2.
- **Embedding swap?** Embed the same chunks with another model, in its own index, because vectors from different models can't be compared. The question must use the same model. Gemini would replace bge in vector search only; BM25, the re-ranker and neighbours stay. Not done yet.
- **What data stays local with bge?** Only the embedding step and local copies. Pinecone holds all chunk text and vectors, and Gemini already gets each question and its retrieved chunks. Gemini embeddings would add the rest of the chunks going to Google.
- **bge vs sentence-transformers?** bge-small is the model; `sentence-transformers` is the Python library that runs it. "Transformer" is the model type, and "sentence" means the token vectors are pooled into one vector for the whole text.
- **Gemini embedding limits:** free-tier `gemini-embedding-2` allows 100 texts per minute, 30,000 tokens per minute and 1,000 texts per day, so indexing 1,714 chunks takes two days of quota. `CachedGeminiEmbeddings` sends 20 texts every 35 s, and a stopped run continues from the cache. `rag/store.py` picks the model with `EMBEDDER=gemini`; the default is bge.
- **Does the embedding model change the vector count?** No. Chunking decides it: one vector per chunk, so 1,714 either way. The token limit only decides how much of each chunk the model reads: bge cuts off 57 chunks at 512 tokens, while `gemini-embedding-2` allows 8,192.
- **Embedding swap, retrieval-only:** Gemini in v3's setup gave no gain (0.974, 0.768, 37/39). Gemini + re-rank 20 without BM25 gave 1.000, 0.787, 38/39. So each layer's value depends on the others: BM25 mainly helps bge here. q22 is still a false hit, and retrieval takes about twice as long.
- **Full-run settings:** `--hybrid` and `--candidates` now also work on full runs, through `answer()`. With no options a run is still v3. `--window` is still for `--retrieval-only` only.
- **v4 Gemini + re-rank 20:** Hit@5 1.000, but Correct stays 37/39 with no flips against v3, and median latency rises from 2.39 s to 3.93 s. Better retrieval metrics don't always mean better answers. Decision: v3 stays the default.
- **Would overlap change the answers?** Untested, so unknown. At most it can fix q22, because q02 and q39 are generation problems, but it can also lose questions. It re-cuts every chunk, so it needs a new index, and `join_chunks()` would need to remove the repeated text.
- **Why wasn't junk cleanup kept?** It lowered retrieval on v1 (Hit@5 0.897 to 0.821), but the cause wasn't investigated, and removing the header also moved every later cut on the page. It wasn't tested with BM25 or neighbours, so it deserves a retest, not a final no.
- **Clean before or after cutting?** Before cutting moves every later cut on the page, so all its chunks change. After cutting changes only the page's first chunk, so any score change comes from removing the junk. Cleaning first is the normal way to build; cleaning after is a fairer test. Re-embedding isn't the issue: the point is knowing which change moved the score.
- **How is the index chosen?** From environment variables read at process start: `EMBEDDER` picks the base name in `rag/store.py`, and `CLEAN` adds `-clean-before` or `-clean-after`. `CLEAN` also sets how BM25's chunks are cut, so search, BM25 and neighbours all use the same version.
- **Junk cleanup retest on v3:** clean after cutting gives 0.949, 0.763, 36/39 (loses q01 by one position). Clean before gives 0.897, 0.694, 34/39. So moved cuts did most of the damage, not removing the junk. Not kept: it gains nothing, and it failed the rule set before the run.
- **Why do moved cuts change retrieval?** A chunk gets one vector for all its text, so search sees the chunk's mix, not each sentence. With clean-before, p15 p39's Table 3 title and rows land in different chunks, and q17 and q34 fall from re-rank 3 and 4 to 8. A reason to prefer structure-aware chunking.
- **Do bigger models always give better results?** Not shown here. Gemini embeddings raised retrieval, but Correct stayed 37/39. q02 and q39 are generation problems and q22 is a re-ranking problem, so check which stage fails before upgrading a model.
- **Query rewriting?** The query is the user's question. Before search, an LLM rewrites it into a form that matches the documents better. It helps most with chat follow-ups ("what about W-4P?"), and costs one extra LLM call per question. Not tested here.
- **`retrieval_latency`:** saved per question next to `latency` from v3 run 2 on. `latency` stays the total, so Gemini time = `latency` minus `retrieval_latency`. Earlier runs only have the total.
- **Gemini free-tier limits:** 15 requests per minute and 500 per day per model. A full eval is about 150 calls.
- **q30 golden fix:** the answer now lists all three fax cases from iss4.pdf p2. The old one left out 855-641-6935.
