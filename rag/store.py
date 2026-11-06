"""INDEXING, fourth box of MAP.md: store vectors + metadata in Pinecone.

Usage: python -m rag.store               (writes the chunk file, creates the bge index if needed, upserts every chunk,
                                          and checks the vector count against the chunk count)
       EMBEDDER=gemini python -m rag.store    (same, for the Gemini index; a stopped run continues from the cache)
Needs PINECONE_API_KEY in .env, and GOOGLE_API_KEY for Gemini.
"""
import os
import time

from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

from rag.embed import EMBEDDERS
from rag.ingest import CLEAN

# Named for the embedding model: a different model is a different vector space, so it gets its own index.
INDEX_NAMES = {"bge": "irs-bge-small-en-v1-5", "gemini": "irs-gemini-embedding-2"}
# Chooses the model for indexing and search, e.g. EMBEDDER=gemini python evals/run.py
EMBEDDER = os.environ.get("EMBEDDER", "bge")
# The free Starter plan only allows serverless indexes in AWS us-east-1.
SPEC = ServerlessSpec(cloud="aws", region="us-east-1")
# Small enough that a batch of 3,072-number vectors stays under Pinecone's 2 MB request limit.
UPSERT_BATCH = 16


def get_index(embedder=EMBEDDER):
    load_dotenv()
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    # Different chunks need their own index too.
    name = INDEX_NAMES[embedder] + (f"-clean-{CLEAN}" if CLEAN else "")
    if not pc.has_index(name):
        pc.create_index(name=name, dimension=EMBEDDERS[embedder].dimensions, metric="cosine", spec=SPEC)
    return pc.Index(name)


def get_store(embedder=EMBEDDER):
    # text_key="text": the chunk text is saved in metadata under "text" and returned with each match.
    return PineconeVectorStore(index=get_index(embedder), embedding=EMBEDDERS[embedder](), text_key="text")


def upsert_chunks(store, chunks):
    # Fixed ids (source:page:chunk_index): re-running overwrites the same vectors instead of adding copies.
    return store.add_documents(chunks, ids=[c.id for c in chunks], batch_size=UPSERT_BATCH)


if __name__ == "__main__":
    from rag.ingest import CHUNKS_FILE, chunk_pages, load_pages, save_chunks

    chunks = chunk_pages(load_pages())
    # Written from the same chunks as the upsert, so BM25 and Pinecone always search the same chunks.
    save_chunks(chunks)
    print(f"saved {len(chunks)} chunks to {CHUNKS_FILE}")
    store = get_store()
    start = time.perf_counter()
    upsert_chunks(store, chunks)
    print(f"upserted {len(chunks)} chunks in {time.perf_counter() - start:.1f}s")
    # Pinecone counts are eventually consistent; give the stats a moment to catch up.
    time.sleep(10)
    stats = store.index.describe_index_stats()
    print(stats)
    if stats.total_vector_count != len(chunks):
        print(f"WARNING: the index has {stats.total_vector_count} vectors but the chunk file has {len(chunks)}")
