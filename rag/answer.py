"""ANSWERING box of MAP.md: question -> top-k chunks -> Gemini -> answer + sources. Baseline v0.

Deliberately naive: no grounding rules, no citations, no abstention (those are Day 5).
Usage: python -m rag.answer "your question"
Needs GOOGLE_API_KEY and PINECONE_API_KEY in .env.
"""
import sys

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from rag.store import get_store

LLM_MODEL = "gemini-3.5-flash-lite"
K = 5
PROMPT = """Answer the question using the context below.

Context:
{context}

Question: {question}"""

_store = _llm = None


def _clients():
    # Built once: loading bge and connecting to Pinecone takes seconds, a question shouldn't.
    global _store, _llm
    if _store is None:
        load_dotenv()
        _store = get_store()
        # temperature 0 so re-running the eval gives (nearly) the same answers.
        _llm = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=0)
    return _store, _llm


def answer(question, k=K):
    store, llm = _clients()
    matches = store.similarity_search_with_score(question, k=k)
    context = "\n\n---\n\n".join(doc.page_content for doc, _ in matches)
    reply = llm.invoke(PROMPT.format(context=context, question=question))
    # sources = retrieved chunks in rank order (rank 1 first); hit@k and MRR are computed from these.
    sources = [
        {"source": doc.metadata["source"], "page": int(doc.metadata["page"]),
         "chunk_index": int(doc.metadata["chunk_index"]), "score": round(score, 4)}
        for doc, score in matches
    ]
    return {"answer": reply.text, "sources": sources}


if __name__ == "__main__":
    result = answer(" ".join(sys.argv[1:]))
    print(result["answer"], "\n")
    for rank, s in enumerate(result["sources"], 1):
        print(f"{rank}. {s['source']} p{s['page']} chunk {s['chunk_index']}  score {s['score']}")
