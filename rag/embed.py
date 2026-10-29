"""INDEXING, third box of MAP.md: embed (local bge-small, cached on disk).

Usage: python -m rag.embed   (embeds every chunk, prints timing and cache hits)
"""
import hashlib
import json
import time
from pathlib import Path

from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer

MODEL = "BAAI/bge-small-en-v1.5"
DIMENSIONS = 384
# bge models expect this instruction on queries only; documents are embedded as-is.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache" / "embeddings"


class CachedBgeEmbeddings(Embeddings):
    """Document vectors are cached by hash(model + text), so unchanged chunks are never re-embedded."""

    def __init__(self, model=MODEL, cache_dir=CACHE_DIR):
        self.model_name = model
        self.model = SentenceTransformer(model)
        self.cache_path = Path(cache_dir) / f"{model.replace('/', '__')}.jsonl"
        self.cache = {}
        if self.cache_path.exists():
            for line in self.cache_path.read_text().splitlines():
                row = json.loads(line)
                self.cache[row["key"]] = row["vector"]
        self.hits = self.misses = 0

    def _key(self, text):
        return hashlib.sha256(f"{self.model_name}\n{text}".encode()).hexdigest()

    def embed_documents(self, texts):
        keys = [self._key(t) for t in texts]
        missing = list({k: t for k, t in zip(keys, texts) if k not in self.cache}.items())
        self.misses += len(missing)
        self.hits += len(texts) - len(missing)
        if missing:
            vectors = self.model.encode([t for _, t in missing], normalize_embeddings=True, batch_size=32)
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            with self.cache_path.open("a") as f:
                for (key, _), vector in zip(missing, vectors):
                    self.cache[key] = vector.tolist()
                    f.write(json.dumps({"key": key, "vector": self.cache[key]}) + "\n")
        return [self.cache[k] for k in keys]

    def embed_query(self, text):
        return self.model.encode(QUERY_PREFIX + text, normalize_embeddings=True).tolist()


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
