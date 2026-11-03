"""ANSWERING box of MAP.md: question -> top-k chunks -> Gemini -> answer + sources. Baseline v0.

Deliberately naive: no grounding rules, no citations, no abstention (those are Day 5).
Usage: python -m rag.answer "your question"
Needs GOOGLE_API_KEY and PINECONE_API_KEY in .env.
"""
import sys
import time

from dotenv import load_dotenv
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_google_genai import ChatGoogleGenerativeAI

from rag.neighbours import SEPARATOR, join_chunks, neighbour_ids
from rag.rerank import get_model as get_reranker, rerank
from rag.store import get_store

LLM_MODEL = "gemini-3.5-flash-lite"
# Free tier allows 15 requests per minute per model; stay under it at 12.
# Shared with the judges, because they use the same model and the same quota.
RATE_LIMITER = InMemoryRateLimiter(requests_per_second=0.2)
K = 5
CANDIDATES = 20  # chunks fetched from Pinecone for the re-ranker; None turns re-ranking off
WINDOW = 1  # chunks added to the context on each side of a match, same page only; 0 turns this off
PROMPT = """Answer the question using the context below.

Context:
{context}

Question: {question}"""

_store = _llm = None


def _get_store():
    # Built once: loading bge and connecting to Pinecone takes seconds, a question shouldn't.
    global _store
    if _store is None:
        load_dotenv()
        _store = get_store()
    return _store


def _get_llm():
    # Separate from the store so retrieval-only evals don't need a Gemini key or quota.
    global _llm
    if _llm is None:
        load_dotenv()
        # No temperature: this model uses fixed sampling and ignores it, so answers may vary between runs.
        _llm = ChatGoogleGenerativeAI(model=LLM_MODEL)
    return _llm


def retrieve(question, k=K, candidates=CANDIDATES, window=WINDOW):
    """Search, optional re-rank and optional neighbours, no LLM. Returns (context text for the prompt, sources)."""
    if candidates:
        found = _get_store().similarity_search_with_score(question, k=candidates)
        matches = rerank(question, [doc for doc, _ in found], k)
    else:
        matches = _get_store().similarity_search_with_score(question, k=k)
    # sources = retrieved chunks in rank order (rank 1 first); hit@k and MRR are computed from these.
    # Neighbours stay out of sources: they weren't ranked, and hit@5 must keep meaning 5 chunks.
    sources = [
        {"source": doc.metadata["source"], "page": int(doc.metadata["page"]),
         "chunk_index": int(doc.metadata["chunk_index"]), "score": round(score, 4)}
        for doc, score in matches
    ]
    if window:
        fetched = _get_store().index.fetch(ids=neighbour_ids(sources, window)).vectors
        context = join_chunks([record.metadata for record in fetched.values()])
    else:
        context = SEPARATOR.join(doc.page_content for doc, _ in matches)
    return context, sources


def answer(question, k=K):
    # Set-up and the wait for quota happen before the clock starts: latency should measure
    # the system, not one-time loading or our free-tier limit.
    _get_store()
    get_reranker()
    llm = _get_llm()
    RATE_LIMITER.acquire()
    start = time.perf_counter()
    context, sources = retrieve(question, k=k)
    reply = llm.invoke(PROMPT.format(context=context, question=question))
    latency = time.perf_counter() - start
    # context = the exact text the model saw; the faithfulness judge checks the answer against it.
    return {"answer": reply.text, "sources": sources, "context": context,
            "latency": round(latency, 3), "tokens": reply.usage_metadata["total_tokens"]}


if __name__ == "__main__":
    result = answer(" ".join(sys.argv[1:]))
    print(result["answer"], "\n")
    for rank, s in enumerate(result["sources"], 1):
        print(f"{rank}. {s['source']} p{s['page']} chunk {s['chunk_index']}  score {s['score']}")
