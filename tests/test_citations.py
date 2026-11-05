"""Pins how the model's citations are checked against the context labels."""

from rag.citations import check_citations, citations_ok

CONTEXT = "[a.pdf, page 1]\nsome text\n\n---\n\n[b.pdf, page 2]\nmore text [c.pdf, page 9] inside the text"


def test_citation_matching_a_label_is_valid():
    assert check_citations("A claim [a.pdf, page 1].", CONTEXT) == {"valid": ["a.pdf, page 1"], "invalid": []}


def test_page_that_was_not_sent_is_invalid():
    assert check_citations("A claim [a.pdf, page 7].", CONTEXT)["invalid"] == ["a.pdf, page 7"]


def test_merged_citation_is_split_and_each_part_checked():
    result = check_citations("A claim [a.pdf, page 1, b.pdf, page 2, a.pdf, page 7].", CONTEXT)
    assert result == {"valid": ["a.pdf, page 1", "b.pdf, page 2"], "invalid": ["a.pdf, page 7"]}


def test_missing_page_word_is_invalid():
    assert check_citations("A claim [a.pdf, 1].", CONTEXT)["invalid"] == ["a.pdf, 1"]


def test_merged_citation_with_missing_page_word_is_split():
    assert check_citations("A claim [a.pdf, 1, b.pdf, 2].", CONTEXT)["invalid"] == ["a.pdf, 1", "b.pdf, 2"]


def test_bracket_inside_a_chunk_is_not_a_label():
    assert check_citations("A claim [c.pdf, page 9].", CONTEXT)["invalid"] == ["c.pdf, page 9"]


def test_answer_with_no_citations_is_not_ok():
    assert not citations_ok(check_citations("A claim with no source.", CONTEXT))


def test_one_invalid_citation_makes_the_answer_not_ok():
    assert not citations_ok(check_citations("One [a.pdf, page 1]. Two [a.pdf, page 7].", CONTEXT))


def test_all_valid_citations_are_ok():
    assert citations_ok(check_citations("One [a.pdf, page 1]. Two [b.pdf, page 2].", CONTEXT))
