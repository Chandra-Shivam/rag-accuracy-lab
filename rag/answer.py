"""ANSWERING box of MAP.md: question -> top-k chunks -> Gemini -> answer + sources.

The prompt has grounding and citation rules (Day 5). The code doesn't check citations yet.
Usage: python -m rag.answer "your question"
Needs GOOGLE_API_KEY and PINECONE_API_KEY in .env.
"""
import sys
import time

from dotenv import load_dotenv
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_google_genai import ChatGoogleGenerativeAI

from rag.hybrid import fuse, get_index as get_keyword_index, keyword_search
from rag.neighbours import SEPARATOR, join_chunks, label, neighbour_ids
from rag.rerank import get_model as get_reranker, rerank
from rag.store import get_store

LLM_MODEL = "gemini-3.5-flash-lite"
# Free tier allows 15 requests per minute per model; stay under it at 12.
# Shared with the judges, because they use the same model and the same quota.
RATE_LIMITER = InMemoryRateLimiter(requests_per_second=0.2)
K = 5
HYBRID_N = 20  # chunks taken from each search before fusion; 0 turns hybrid off
# Chunks sent to the re-ranker; None turns re-ranking off. 2 * HYBRID_N, so fusion can never cut a chunk.
# With 20, fusion cut q36's gold chunks before the re-ranker saw them (EXPERIMENTS.md).
CANDIDATES = 2 * HYBRID_N
WINDOW = 1  # chunks added to the context on each side of a match, same page only; 0 turns this off
REFUSAL = "I don't have enough information to answer the question."
PROMPT = """Answer the question using the context below. Each block of the context starts with a label in the form [source, page N].

Rules:
1. Use only the context, not outside knowledge. If the answer can be calculated from numbers in the context, calculate it. If the context does not contain the answer, say "{refusal}" If it covers only part of the question, answer that part and say what is missing.
2. After each claim, cite the label of the block it came from, copied exactly. Cite one label per bracket. Never cite a page number printed in the text.
3. Copy dates and amounts exactly as the context gives them. If a date has no year and the context makes the year clear, include the year.

Context:
{context}

Question: {question}"""

_store = _llm = None


def is_refusal(text):
    """True only for the exact refusal. A refusal with other claims in it is still an answer to check."""
    return text.strip() == REFUSAL


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


def retrieve(question, k=K, candidates=CANDIDATES, window=WINDOW, hybrid=HYBRID_N):
    """Search, optional hybrid, re-rank and neighbours, no LLM. Returns (context text for the prompt, sources)."""
    if candidates:
        found = _get_store().similarity_search_with_score(question, k=hybrid or candidates)
        docs = [doc for doc, _ in found]
        if hybrid:
            docs = fuse(docs, keyword_search(question, hybrid), candidates)
        matches = rerank(question, docs, k)
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
        context = SEPARATOR.join(label(doc.metadata["source"], doc.metadata["page"]) + doc.page_content
                                 for doc, _ in matches)
    return context, sources


def answer(question, k=K, candidates=CANDIDATES, hybrid=HYBRID_N):
    # Set-up and the wait for quota happen before the clock starts: latency should measure
    # the system, not one-time loading or our free-tier limit.
    _get_store()
    get_reranker()
    get_keyword_index()
    llm = _get_llm()
    RATE_LIMITER.acquire()
    start = time.perf_counter()
    context, sources = retrieve(question, k=k, candidates=candidates, hybrid=hybrid)
    retrieval_latency = time.perf_counter() - start
    reply = llm.invoke(PROMPT.format(refusal=REFUSAL, context=context, question=question))
    latency = time.perf_counter() - start
    # context = the exact text the model saw; the faithfulness judge checks the answer against it.
    return {"answer": reply.text, "sources": sources, "context": context, "latency": round(latency, 3),
            "retrieval_latency": round(retrieval_latency, 3), "tokens": reply.usage_metadata["total_tokens"]}


if __name__ == "__main__":
    result = answer(" ".join(sys.argv[1:]))
    print(result["answer"], "\n")
    for rank, s in enumerate(result["sources"], 1):
        print(f"{rank}. {s['source']} p{s['page']} chunk {s['chunk_index']}  score {s['score']}")
