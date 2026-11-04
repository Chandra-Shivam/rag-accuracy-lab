"""INDEXING, third box of MAP.md: embed (local bge-small or Gemini, cached on disk).

Usage: python -m rag.embed   (embeds every chunk with bge, prints timing and cache hits)
"""
import hashlib
import json
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sentence_transformers import SentenceTransformer

MODEL = "BAAI/bge-small-en-v1.5"
DIMENSIONS = 384
# bge models expect this instruction on queries only; documents are embedded as-is.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
GEMINI_MODEL = "gemini-embedding-2"
GEMINI_DIMENSIONS = 3072
# gemini-embedding-2 takes its task in the prompt text, with different formats for each side of the search.
GEMINI_QUERY_PREFIX = "task: question answering | query: "
GEMINI_DOCUMENT_PREFIX = "title: none | text: "
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache" / "embeddings"


class CachedEmbeddings(Embeddings):
    """Document vectors are cached by hash(model + text), so unchanged chunks are never re-embedded."""

    batch_size = 32
    pause = 0  # seconds between batches, for APIs with a per-minute limit

    def __init__(self, model, cache_dir=CACHE_DIR):
        self.model_name = model
        self.cache_path = Path(cache_dir) / f"{model.replace('/', '__')}.jsonl"
        self.cache = {}
        if self.cache_path.exists():
            for line in self.cache_path.read_text().splitlines():
                row = json.loads(line)
                self.cache[row["key"]] = row["vector"]
        self.hits = self.misses = 0

    def _key(self, text):
        return hashlib.sha256(f"{self.model_name}\n{text}".encode()).hexdigest()

    def _encode_documents(self, texts):
        raise NotImplementedError

    def embed_documents(self, texts):
        keys = [self._key(t) for t in texts]
        missing = list({k: t for k, t in zip(keys, texts) if k not in self.cache}.items())
        self.misses += len(missing)
        self.hits += len(texts) - len(missing)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        # Saved after every batch, so a stop (e.g. API quota) loses at most the batch in progress.
        for start in range(0, len(missing), self.batch_size):
            if start:
                time.sleep(self.pause)
            batch = missing[start : start + self.batch_size]
            vectors = self._encode_documents([t for _, t in batch])
            with self.cache_path.open("a") as f:
                for (key, _), vector in zip(batch, vectors):
                    self.cache[key] = vector
                    f.write(json.dumps({"key": key, "vector": vector}) + "\n")
        return [self.cache[k] for k in keys]


class CachedBgeEmbeddings(CachedEmbeddings):
    dimensions = DIMENSIONS

    def __init__(self, model=MODEL, cache_dir=CACHE_DIR):
        super().__init__(model, cache_dir)
        self.model = SentenceTransformer(model)

    def _encode_documents(self, texts):
        return self.model.encode(texts, normalize_embeddings=True, batch_size=self.batch_size).tolist()

    def embed_query(self, text):
        return self.model.encode(QUERY_PREFIX + text, normalize_embeddings=True).tolist()


class CachedGeminiEmbeddings(CachedEmbeddings):
    """client lets tests skip the API."""

    dimensions = GEMINI_DIMENSIONS
    # The free tier allows 100 texts and 30,000 tokens per minute, and our largest chunks are about 680 tokens.
    batch_size = 20
    pause = 35

    def __init__(self, model=GEMINI_MODEL, cache_dir=CACHE_DIR, client=None):
        super().__init__(model, cache_dir)
        load_dotenv()
        self.client = client or GoogleGenerativeAIEmbeddings(model=model)

    def _encode_documents(self, texts):
        return self.client.embed_documents([GEMINI_DOCUMENT_PREFIX + t for t in texts])

    def embed_query(self, text):
        return self.client.embed_query(GEMINI_QUERY_PREFIX + text)


EMBEDDERS = {"bge": CachedBgeEmbeddings, "gemini": CachedGeminiEmbeddings}


if __name__ == "__main__":
    from rag.ingest import chunk_pages, load_pages

    chunks = chunk_pages(load_pages())
    start = time.perf_counter()
    embedder = CachedBgeEmbeddings()
    loaded = time.perf_counter()
    vectors = embedder.embed_documents([c.page_content for c in chunks])
    done = time.perf_counter()
    print(f"model load {loaded - start:.1f}s, embed {done - loaded:.1f}s for {len(vectors)} chunks")
    print(f"cache hits {embedder.hits}, misses {embedder.misses}, dimensions {len(vectors[0])}")
