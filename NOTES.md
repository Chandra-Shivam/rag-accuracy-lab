# Notes

Quick reference for the flow, the files and answers to past doubts. Keep each entry to 1–2 lines.

## Flow (see MAP.md)

| Box | File / function | In → out |
|---|---|---|
| load pages | `rag/ingest.py` `load_pages()` | PDFs → one Document per page, metadata `source`, `page` (1-based) |
| chunk | `rag/ingest.py` `chunk_pages()` | pages → 1,000-char slices, metadata + `chunk_index`, id `source:page:index` |
| embed | `rag/embed.py` `CachedBgeEmbeddings` | text → 384-number vector (bge-small), cached on disk |
| store | `rag/store.py` `get_store()`, `upsert_chunks()` | chunks → vectors + metadata in Pinecone index `irs-bge-small-en-v1-5` |
| answer | `rag/answer.py` `answer()` | question → top-5 chunks → `gemini-3.5-flash-lite` (temp 0) → `{answer, sources}` (sources in rank order) |
| measure | `evals/` | golden set → metrics → EXPERIMENTS.md row |

## Files

- **corpus/SOURCES.md**: list of the 20 IRS PDFs (URL, revision, page count). PDFs aren't in git.
- **corpus/download.py**: rebuilds `corpus/` from SOURCES.md and warns if a page count changed.
- **evals/golden.jsonl**: the exam: question, correct answer, type, gold pages.
- **evals/golden_evidence.jsonl**: the proof: an exact quote from each gold page; `absent` words for unanswerable questions.
- **evals/validate_golden.py**: checks the format of golden.jsonl, and that each quote really is on its gold page.
- **rag/ingest.py**: `load_pages()` loads and converts page numbers (+1, the only place this happens); `chunk_pages()` slices pages into chunks.
- **rag/embed.py**: `embed_documents()` embeds only texts that aren't in the cache; `embed_query()` adds the bge prefix and isn't cached.
- **rag/store.py**: creates the Pinecone index if missing (384 dims, cosine, free plan = AWS us-east-1) and upserts chunks by fixed id. Key comes from `.env`.
- **rag/answer.py**: `answer(question)` retrieves top-k, sends a naive prompt to Gemini, returns the answer and the retrieved pages. Same function for every version.
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
- **Failure stages:** ingestion (bad text/tables), retrieval (gold page not in top-k), generation (wrong answer or no abstention). Label every failure by stage.
