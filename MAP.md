INDEXING (once, offline)
  PDFs → load pages → chunk → embed → store in Pinecone
         (page numbers) (chunk size,  (bge-small,  (index, metadata)
                         overlap)      384 dims)

ANSWERING (every question)
  question → embed → retrieve top-k → (re-rank) → prompt + chunks → LLM → answer + citations
                     (hybrid search)                (grounding,          (abstention)
                                                     citations)

SERVING (every request, api.py)
  POST /ask        → answer()        → JSON: answer, sources, citations
  POST /ask/stream → stream_answer() → SSE events: sources, then tokens, then done (citations)
  GET /            → static/index.html: streams the answer, links the cited sources (IRS URL #page=N)

MEASURING (every experiment)
  golden set → run every question → retrieval metrics (hit@k, MRR) + answer metrics (judge)
             → EXPERIMENTS.md row