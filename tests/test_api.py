from api import URLS, with_urls


def test_every_corpus_file_has_a_url():
    assert len(URLS) == 20
    assert URLS["p15.pdf"] == "https://www.irs.gov/pub/irs-pdf/p15.pdf"


def test_with_urls_adds_page_link_and_keeps_fields():
    sources = [{"source": "fw4.pdf", "page": 3, "chunk_index": 1, "score": 0.9}]
    assert with_urls(sources) == [
        {"source": "fw4.pdf", "page": 3, "chunk_index": 1, "score": 0.9,
         "url": "https://www.irs.gov/pub/irs-pdf/fw4.pdf#page=3"}
    ]
