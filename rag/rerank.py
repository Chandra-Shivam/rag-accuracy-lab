"""ANSWERING box of MAP.md: re-score retrieved chunks with a cross-encoder and keep the best k.

Vector search compares two separate vectors. A cross-encoder reads the question and chunk
together, so it is slower but can be more accurate. It runs locally, with no API calls.
"""
from sentence_transformers import CrossEncoder

MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

_model = None


def get_model():
    # Built once: loading the model takes seconds, a question shouldn't.
    global _model
    if _model is None:
        _model = CrossEncoder(MODEL)
    return _model


def rerank(question, docs, k, score_pairs=None):
    """Returns the best k as (doc, score), highest score first. score_pairs lets tests skip the model."""
    if not docs:
        return []
    score_pairs = score_pairs or get_model().predict
    scores = score_pairs([(question, doc.page_content) for doc in docs])
    ranked = sorted(zip(docs, scores), key=lambda pair: pair[1], reverse=True)
    return [(doc, float(score)) for doc, score in ranked[:k]]
