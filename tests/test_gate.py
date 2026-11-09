"""Canary tests for the eval gate: a good run passes, and every kind of bad run fails.

These test the reader, not the judge: a gate that always passed would still let every run through.
"""

from evals.gate import check_complete, gate
from rag.answer import REFUSAL

GOLDEN = [{"id": "q1", "type": "single_fact"}, {"id": "q2", "type": "single_fact"},
          {"id": "q3", "type": "unanswerable"}]
MINIMUMS = {"correct": 0.5, "abstained": 1.0}


def good_run():
    return [
        {"id": "q1", "answer": "A [a.pdf, page 1].", "hit": True, "evidence": True, "correct": True, "faithful": True},
        {"id": "q2", "answer": "B [a.pdf, page 2].", "hit": True, "evidence": True, "correct": False, "faithful": True},
        {"id": "q3", "answer": REFUSAL, "abstained": True},
    ]


def test_good_run_passes():
    assert gate(GOLDEN, good_run(), MINIMUMS) == ["x"]


def test_low_score_fails():
    rows = good_run()
    rows[0]["correct"] = False
    assert gate(GOLDEN, rows, MINIMUMS) == ["correct: 0.000 is below the minimum 0.500"]


def test_missing_question_fails_even_with_good_scores():
    # Without q2, Correct is 1/1, which looks better than the full run's 1/2.
    rows = [r for r in good_run() if r["id"] != "q2"]
    assert gate(GOLDEN, rows, MINIMUMS) == ["missing questions: q2"]


def test_duplicate_and_unknown_questions_fail():
    rows = good_run() + [good_run()[0], {**good_run()[0], "id": "q9"}]
    assert check_complete(GOLDEN, rows) == ["duplicate questions: q1", "questions not in the golden set: q9"]


def test_row_without_a_required_score_fails():
    rows = good_run()
    del rows[1]["correct"]
    del rows[1]["faithful"]
    assert check_complete(GOLDEN, rows) == ["no correct on 1 rows: q2", "no faithful on 1 rows: q2"]


def test_exact_refusal_needs_no_faithful_score():
    rows = good_run()
    rows[0] = {"id": "q1", "answer": REFUSAL, "hit": True, "evidence": True, "correct": False}
    assert check_complete(GOLDEN, rows) == []


def test_gate_without_minimums_fails():
    assert gate(GOLDEN, good_run(), {}) == ["no minimums set"]


def test_metric_no_row_has_fails():
    assert gate(GOLDEN, good_run(), {"citations_ok": 0.9}) == ["citations_ok: no rows have it"]
