"""Pins the hit@k and MRR definitions from PLAN.md (Day 3)."""

from evals.metrics import is_hit, reciprocal_rank


def page(source, number):
    return {"source": source, "page": number}


A, B, C = page("a.pdf", 1), page("b.pdf", 2), page("c.pdf", 3)


def test_hit_needs_all_gold_pages():
    assert is_hit([A], [C, A])
    assert is_hit([A, B], [B, C, A])
    assert not is_hit([A, B], [A, C]), "one of two gold pages is not a hit"


def test_same_page_number_in_another_document_is_a_miss():
    assert not is_hit([page("a.pdf", 2)], [B])
    assert reciprocal_rank([page("a.pdf", 2)], [B]) == 0.0


def test_reciprocal_rank_uses_first_gold_page():
    assert reciprocal_rank([A], [A, B]) == 1.0
    assert reciprocal_rank([A], [B, C, A]) == 1 / 3
    assert reciprocal_rank([A, B], [C, B, A]) == 1 / 2, "first gold page found counts"
    assert reciprocal_rank([A], [B, C]) == 0.0


def test_extra_fields_on_retrieved_chunks_are_ignored():
    chunk = {**A, "chunk_index": 4, "score": 0.81}
    assert is_hit([A], [chunk])
    assert reciprocal_rank([A], [chunk]) == 1.0
