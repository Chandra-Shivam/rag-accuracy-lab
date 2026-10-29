INDEXING (once, offline)
  PDFs → load pages → chunk → embed → store in Pinecone
         (page numbers) (chunk size,  (bge-small,  (index, metadata)
                         overlap)      384 dims)

ANSWERING (every question)
  question → embed → retrieve top-k → (re-rank) → prompt + chunks → LLM → answer + citations
                     (hybrid search)                (grounding,          (abstention)
                                                     citations)

MEASURING (every experiment)
  golden set → run every question → retrieval metrics (hit@k, MRR) + answer metrics (judge)
             → EXPERIMENTS.md row