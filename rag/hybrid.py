"""ANSWERING box of MAP.md: keyword search (BM25) and Reciprocal Rank Fusion with vector search.

Vector search matches meaning, so it can mix up exact codes such as W-4S and W-4P. BM25 matches
exact words and gives rare words more weight. The BM25 index runs locally and is built from the
same chunks as Pinecone, with no API calls.
"""
import re
from collections import defaultdict

from rank_bm25 import BM25Okapi

from rag.ingest import chunk_pages, load_pages

RRF_K = 60  # from the original RRF paper; a common default that stops rank 1 from dominating
# Keeps "w-4s" and "6.0" as one token. Split up, "w-4s" would also match every other W form.
TOKEN = re.compile(r"[a-z0-9$%]+(?:[-.,][a-z0-9$%]+)*")

_index = None


def tokenize(text):
    return TOKEN.findall(text.lower())


def build_index(chunks):
    return BM25Okapi([tokenize(chunk.page_content) for chunk in chunks]), chunks


def get_index():
    # Built once: reading the PDFs takes seconds, a question shouldn't.
    global _index
    if _index is None:
        _index = build_index(chunk_pages(load_pages()))
    return _index


def keyword_search(question, n, index=None):
    """Returns up to n chunks, best first. index lets tests use a small corpus."""
    bm25, chunks = index or get_index()
    scores = bm25.get_scores(tokenize(question))
    ranked = sorted(zip(chunks, scores), key=lambda pair: pair[1], reverse=True)
    # Score 0 means no question word is in the chunk, so it isn't a keyword match.
    return [chunk for chunk, score in ranked[:n] if score > 0]


def chunk_id(doc):
    # Pinecone returns numbers in metadata as floats, so convert before comparing with local chunks.
    return f"{doc.metadata['source']}:{int(doc.metadata['page'])}:{int(doc.metadata['chunk_index'])}"


def fuse(vector_docs, keyword_docs, limit, k=RRF_K):
    """Reciprocal Rank Fusion: each chunk scores 1 / (k + rank) per list, and its scores are added."""
    scores, docs = defaultdict(float), {}
    for ranked in (vector_docs, keyword_docs):
        for rank, doc in enumerate(ranked, 1):
            scores[chunk_id(doc)] += 1 / (k + rank)
            docs[chunk_id(doc)] = doc
    best = sorted(scores, key=scores.get, reverse=True)
    return [docs[key] for key in best[:limit]]
