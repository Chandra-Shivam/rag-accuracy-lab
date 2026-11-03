"""Pins keyword search and Reciprocal Rank Fusion, without Pinecone or the PDFs."""

from langchain_core.documents import Document

from rag.hybrid import build_index, fuse, keyword_search, tokenize


def chunk(index, text="", page=1):
    return Document(page_content=text, metadata={"source": "a.pdf", "page": page, "chunk_index": index})


def indexes(docs):
    return [doc.metadata["chunk_index"] for doc in docs]


A, B, C, D = chunk(0), chunk(1), chunk(2), chunk(3)


def test_tokenize_keeps_form_names_and_numbers_whole():
    assert tokenize("Form W-4S, at 6.0%.") == ["form", "w-4s", "at", "6.0%"]


def test_keyword_search_tells_form_names_apart():
    chunks = [chunk(0, "give form w-4p to the payer"), chunk(1, "give form w-4s to the payer"),
              chunk(2, "tables for wages"), chunk(3, "deposit rules")]
    assert indexes(keyword_search("w-4s", 5, build_index(chunks))) == [1]


def test_keyword_search_ranks_the_rare_word_first():
    chunks = [chunk(0, "form payer"), chunk(1, "form sick"), chunk(2, "form wages"), chunk(3, "form rules"),
              chunk(4, "form tables"), chunk(5, "deposit")]
    assert indexes(keyword_search("form sick", 5, build_index(chunks)))[0] == 1


def test_keyword_search_keeps_only_n():
    chunks = [chunk(i, "sick pay") for i in range(3)] + [chunk(i, "wages") for i in range(3, 10)]
    assert len(keyword_search("sick", 2, build_index(chunks))) == 2


def test_chunk_in_both_lists_beats_rank_1_in_one_list():
    # A = 1/61, B = 1/63 + 1/62, C = 1/61, D = 1/62
    assert indexes(fuse([A, D, B], [C, B], 4))[0] == 1


def test_fuse_uses_the_rrf_formula():
    # B = 1/62 + 1/90 is above A = 1/61 only if both scores are added.
    keyword_docs = [chunk(i) for i in range(10, 39)] + [B]
    assert indexes(fuse([A, B], keyword_docs, 2)) == [1, 0]
    # With k = 0 the same lists give A = 1/1 and B = 1/2 + 1/30, so A wins.
    assert indexes(fuse([A, B], keyword_docs, 1, k=0)) == [0]


def test_fuse_keeps_only_limit_and_no_duplicates():
    assert indexes(fuse([A, B], [B, A], 5)) == [0, 1]
    assert len(fuse([A, B], [C, D], 3)) == 3


def test_fuse_matches_pinecone_float_metadata_with_local_ints():
    from_pinecone = Document(page_content="", metadata={"source": "a.pdf", "page": 1.0, "chunk_index": 0.0})
    assert len(fuse([from_pinecone], [A], 5)) == 1


def test_keyword_only_chunk_can_enter_the_list():
    assert 2 in indexes(fuse([A, B], [C], 3))
