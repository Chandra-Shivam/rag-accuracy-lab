"""Pins the page-number convention from PLAN.md (Day 2, task 1) and the print-proof header cleanup."""

from langchain_core.documents import Document

from rag.ingest import chunk_pages, clean_page, load_pages
from pathlib import Path



FIXTURES = Path(__file__).parent / "fixtures"


def test_pages_are_one_based():
    pages = load_pages(corpus=FIXTURES)
    pages_number = [p.metadata["page"] for p in pages]

    assert min(pages_number) == 1, "pages are 0-based"
    assert list(range(1,3)) == pages_number, "Wrong Pages or Pages Dropped"


HEADER = "Page 7 of 71  Fileid: x/source 15:14\nproofs. MUST be removed before printing.\n"


def page(text):
    return Document(page_content=text, metadata={"source": "a.pdf", "page": 1})


def texts(pages_text, **kwargs):
    return [c.page_content for c in chunk_pages([page(pages_text)], size=10, **kwargs)]


def test_clean_page_removes_both_header_layouts():
    assert clean_page(HEADER + "Table 2") == "Table 2"
    assert clean_page("Userid: CPM\nproofs. MUST be removed before printing.\nForm") == "Form"


def test_clean_page_keeps_text_around_a_mid_page_header():
    assert clean_page("before " + HEADER + "after") == "before after"


def test_clean_page_leaves_other_pages_unchanged():
    text = "Page 7 of 71 says this MUST be removed before printing."
    assert clean_page(text) == text, "no Fileid, so not the proof header"


def test_no_cleaning_keeps_the_header():
    assert "".join(texts(HEADER + "body", clean=None)) == HEADER + "body"
    assert "".join(texts(HEADER + "body")) == HEADER + "body", "cleaning is off by default"


def test_cleaning_before_moves_the_cuts():
    body = "a" * 8 + "b" * 8
    assert texts(HEADER + body, clean="before") == ["a" * 8 + "bb", "b" * 6]


def test_cleaning_after_keeps_the_cuts():
    # The first 10 characters are plain text, so the first chunk matches a page with no cleaning.
    text = "0123456789" + "abcd" + HEADER + "efghij"
    plain = texts(text, clean=None)
    cleaned = texts(text, clean="after")
    assert len(cleaned) == len(plain), "same cuts means the same number of chunks"
    assert cleaned[0] == "0123456789"
    assert "".join(cleaned) == "0123456789abcdefghij"
    assert "MUST" not in "".join(cleaned)


def test_cleaning_after_only_changes_chunks_touching_the_header():
    text = HEADER + "x" * 25
    plain, cleaned = texts(text, clean=None), texts(text, clean="after")
    assert cleaned[-2:] == plain[-2:]
    assert cleaned[0] == ""
    assert "".join(cleaned) == "x" * 25
