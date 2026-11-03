"""Pins how two runs are compared, question by question."""

from evals.compare import find_flips


def test_lists_only_questions_whose_value_changed():
    before = {"q1": {"correct": True}, "q2": {"correct": False}, "q3": {"correct": True}}
    after = {"q1": {"correct": True}, "q2": {"correct": True}, "q3": {"correct": False}}
    assert find_flips(before, after, "correct") == [("q2", False, True), ("q3", True, False)]


def test_equal_totals_can_still_have_flips():
    before = {"q1": {"correct": True}, "q2": {"correct": False}}
    after = {"q1": {"correct": False}, "q2": {"correct": True}}
    assert len(find_flips(before, after, "correct")) == 2


def test_question_in_only_one_run_is_skipped():
    before = {"q1": {"correct": True}}
    after = {"q1": {"correct": True}, "q2": {"correct": False}}
    assert find_flips(before, after, "correct") == []


def test_metric_a_question_does_not_have_is_skipped():
    before = {"q1": {"abstained": True}}
    after = {"q1": {"abstained": True}}
    assert find_flips(before, after, "correct") == []
