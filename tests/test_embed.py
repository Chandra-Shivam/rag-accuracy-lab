"""Pins the embedding cache and the Gemini prompt formats, without any model or API."""

import pytest

from rag.embed import CachedEmbeddings, CachedGeminiEmbeddings, GEMINI_DOCUMENT_PREFIX, GEMINI_QUERY_PREFIX


class FakeEmbeddings(CachedEmbeddings):
    batch_size = 2

    def __init__(self, cache_dir, fail_on_batch=None, model="fake"):
        super().__init__(model, cache_dir)
        self.batches = []
        self.fail_on_batch = fail_on_batch

    def _encode_documents(self, texts):
        self.batches.append(texts)
        if len(self.batches) == self.fail_on_batch:
            raise RuntimeError("quota")
        return [[float(len(t))] for t in texts]

    def embed_query(self, text):
        return [0.0]


def test_returns_vectors_in_input_order_with_duplicates(tmp_path):
    assert FakeEmbeddings(tmp_path).embed_documents(["aaa", "b", "aaa"]) == [[3.0], [1.0], [3.0]]


def test_embeds_in_batches(tmp_path):
    embedder = FakeEmbeddings(tmp_path)
    embedder.embed_documents(["a", "b", "c"])
    assert embedder.batches == [["a", "b"], ["c"]]


def test_cached_text_is_not_embedded_again_after_a_restart(tmp_path):
    FakeEmbeddings(tmp_path).embed_documents(["a", "b"])
    embedder = FakeEmbeddings(tmp_path)
    assert embedder.embed_documents(["a", "b", "ccc"]) == [[1.0], [1.0], [3.0]]
    assert embedder.batches == [["ccc"]]
    assert (embedder.hits, embedder.misses) == (2, 1)


def test_a_stop_keeps_the_finished_batches(tmp_path):
    with pytest.raises(RuntimeError):
        FakeEmbeddings(tmp_path, fail_on_batch=2).embed_documents(["a", "b", "c", "d"])
    embedder = FakeEmbeddings(tmp_path)
    embedder.embed_documents(["a", "b", "c", "d"])
    assert embedder.batches == [["c", "d"]]


def test_pauses_between_batches_only(tmp_path, monkeypatch):
    pauses = []
    monkeypatch.setattr("rag.embed.time.sleep", pauses.append)
    embedder = FakeEmbeddings(tmp_path)
    embedder.pause = 7
    embedder.embed_documents(["a", "b", "c", "d"])
    assert pauses == [7], "2 batches need 1 pause"


def test_different_models_do_not_share_vectors(tmp_path):
    FakeEmbeddings(tmp_path, model="one").embed_documents(["a"])
    embedder = FakeEmbeddings(tmp_path, model="two")
    embedder.embed_documents(["a"])
    assert embedder.batches == [["a"]]
    assert embedder._key("a") != FakeEmbeddings(tmp_path, model="one")._key("a"), "key includes the model"


class FakeClient:
    def __init__(self):
        self.seen = []

    def embed_documents(self, texts):
        self.seen.extend(texts)
        return [[1.0] for _ in texts]

    def embed_query(self, text):
        self.seen.append(text)
        return [1.0]


def test_gemini_uses_a_different_format_for_documents_and_queries(tmp_path):
    client = FakeClient()
    embedder = CachedGeminiEmbeddings(cache_dir=tmp_path, client=client)
    embedder.embed_documents(["chunk"])
    embedder.embed_query("question")
    assert client.seen == [GEMINI_DOCUMENT_PREFIX + "chunk", GEMINI_QUERY_PREFIX + "question"]
