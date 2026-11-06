"""Pins what counts as a refusal, that the prompt asks for that exact text, and the stream's event order."""

from types import SimpleNamespace

import rag.answer
from rag.answer import PROMPT, REFUSAL, is_refusal, stream_answer


def test_exact_refusal_is_a_refusal():
    assert is_refusal(REFUSAL)
    assert is_refusal(f"\n{REFUSAL} \n")


def test_refusal_with_other_claims_is_not_a_refusal():
    assert not is_refusal(f"{REFUSAL} The 2026 limit is $184,500 [p15.pdf, page 2].")


def test_prompt_contains_the_exact_refusal():
    assert REFUSAL in PROMPT.format(refusal=REFUSAL, context="c", question="q")


def test_stream_sends_sources_then_tokens_then_citations(monkeypatch):
    # Fakes for retrieval and Gemini, so the test needs no Pinecone, models or quota.
    pieces = ["The limit ", "", "is $6,000 ", "[a.pdf, page 1]."]
    fake_llm = SimpleNamespace(stream=lambda prompt: (SimpleNamespace(text=p) for p in pieces))
    sources = [{"source": "a.pdf", "page": 1, "chunk_index": 0, "score": 1.0}]
    monkeypatch.setattr(rag.answer, "_ready", lambda: fake_llm)
    monkeypatch.setattr(rag.answer, "retrieve", lambda question, **kwargs: ("[a.pdf, page 1]\ntext", sources))

    events = list(stream_answer("q"))

    assert events[0] == ("sources", sources)
    # The empty piece is skipped.
    assert events[1:-1] == [("token", "The limit "), ("token", "is $6,000 "), ("token", "[a.pdf, page 1].")]
    assert events[-1] == ("done", {"citations": {"valid": ["a.pdf, page 1"], "invalid": []}})
