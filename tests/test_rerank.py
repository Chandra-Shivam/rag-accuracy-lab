"""Pins how re-ranking orders and cuts chunks, without loading the model."""

from langchain_core.documents import Document

from rag.rerank import rerank


def doc(text):
    return Document(page_content=text)


def fake_scores(scores):
    return lambda pairs: [scores[text] for _, text in pairs]


def test_orders_by_score_not_by_input_order():
    docs = [doc("low"), doc("high"), doc("mid")]
    result = rerank("q", docs, 3, fake_scores({"low": 0.1, "high": 0.9, "mid": 0.5}))
    assert [d.page_content for d, _ in result] == ["high", "mid", "low"]


def test_keeps_only_k():
    docs = [doc("a"), doc("b"), doc("c")]
    result = rerank("q", docs, 2, fake_scores({"a": 3, "b": 2, "c": 1}))
    assert [d.page_content for d, _ in result] == ["a", "b"]


def test_scorer_sees_the_question_with_each_chunk():
    seen = []

    def score(pairs):
        seen.extend(pairs)
        return [1.0] * len(pairs)

    rerank("the question", [doc("chunk")], 1, score)
    assert seen == [("the question", "chunk")]


def test_no_docs_returns_nothing():
    assert rerank("q", [], 5, fake_scores({})) == []
