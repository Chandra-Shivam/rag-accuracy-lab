"""Pins the hit@k and MRR definitions from PLAN.md (Day 3)."""

from evals.metrics import evidence_found, is_hit, reciprocal_rank, summarize


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


def test_summarize_uses_only_rows_that_have_the_metric():
    rows = [
        {"hit": True, "rr": 1.0, "correct": True, "faithful": True, "latency": 1.0, "tokens": 100},
        {"hit": False, "rr": 0.0, "correct": False, "faithful": True, "latency": 3.0, "tokens": 300},
        {"abstained": False, "faithful": False, "latency": 2.0, "tokens": 200},
    ]
    result = summarize(rows)
    assert result["hit"] == 0.5, "unanswerable rows don't count towards hit"
    assert result["correct"] == 0.5, "unanswerable rows don't count towards correct"
    assert result["faithful"] == 2 / 3, "every row counts towards faithful"
    assert result["abstained"] == 0.0, "only unanswerable rows count towards abstained"
    assert result["latency"] == 2.0
    assert result["tokens"] == 200


def test_summarize_returns_none_for_a_metric_no_row_has():
    assert summarize([{"hit": True, "rr": 1.0}])["correct"] is None


def quote(text):
    return {"source": "a.pdf", "page": 1, "quote": text}


def test_evidence_needs_all_quotes():
    context = "Weekly $309.60 and Biweekly 619.20"
    assert evidence_found([quote("Weekly $309.60"), quote("Biweekly 619.20")], context)
    assert not evidence_found([quote("Weekly $309.60"), quote("Monthly 1,341.70")], context)


def test_evidence_ignores_pdf_line_breaks_and_hyphens():
    assert evidence_found([quote("each employee as wages")], "each em-\nployee as wages")


def test_evidence_keeps_digits_exact():
    assert not evidence_found([quote("rate is 6.0%")], "rate is 0.6%")


def test_extra_fields_on_retrieved_chunks_are_ignored():
    chunk = {**A, "chunk_index": 4, "score": 0.81}
    assert is_hit([A], [chunk])
    assert reciprocal_rank([A], [chunk]) == 1.0
