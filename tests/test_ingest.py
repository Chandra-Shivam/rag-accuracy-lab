"""Pins the page-number convention from PLAN.md (Day 2, task 1)."""

from rag.ingest import load_pages
from pathlib import Path



FIXTURES = Path(__file__).parent / "fixtures"


def test_pages_are_one_based():
    pages = load_pages(corpus=FIXTURES)
    pages_number = [p.metadata["page"] for p in pages]

    assert min(pages_number) == 1, "pages are 0-based"
    assert list(range(1,3)) == pages_number, "Wrong Pages or Pages Dropped"
