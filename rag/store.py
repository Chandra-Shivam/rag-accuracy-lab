"""INDEXING, fourth box of MAP.md: store vectors + metadata in Pinecone.

Usage: python -m rag.store   (creates the index if needed, upserts every chunk, prints the vector count)
Needs PINECONE_API_KEY in .env.
"""
import os
import time

from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

from rag.embed import DIMENSIONS, CachedBgeEmbeddings

# Named for the embedding model: a different model is a different vector space, so it gets its own index.
INDEX_NAME = "irs-bge-small-en-v1-5"
# The free Starter plan only allows serverless indexes in AWS us-east-1.
SPEC = ServerlessSpec(cloud="aws", region="us-east-1")


def get_index(name=INDEX_NAME):
    load_dotenv()
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    if not pc.has_index(name):
        pc.create_index(name=name, dimension=DIMENSIONS, metric="cosine", spec=SPEC)
    return pc.Index(name)


def get_store(embedder=None, name=INDEX_NAME):
    # text_key="text": the chunk text is saved in metadata under "text" and returned with each match.
    return PineconeVectorStore(index=get_index(name), embedding=embedder or CachedBgeEmbeddings(), text_key="text")


def upsert_chunks(store, chunks):
    # Fixed ids (source:page:chunk_index): re-running overwrites the same vectors instead of adding copies.
    return store.add_documents(chunks, ids=[c.id for c in chunks])


if __name__ == "__main__":
    from rag.ingest import chunk_pages, load_pages

    chunks = chunk_pages(load_pages())
    store = get_store()
    start = time.perf_counter()
    upsert_chunks(store, chunks)
    print(f"upserted {len(chunks)} chunks in {time.perf_counter() - start:.1f}s")
    # Pinecone counts are eventually consistent; give the stats a moment to catch up.
    time.sleep(10)
    print(store.index.describe_index_stats())
