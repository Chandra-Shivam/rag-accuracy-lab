"""Pins which neighbouring chunks are fetched and how they join, without Pinecone."""

from rag.neighbours import SEPARATOR, join_chunks, neighbour_ids


def source(page, index, name="a.pdf"):
    return {"source": name, "page": page, "chunk_index": index}


def record(page, index, text, name="a.pdf"):
    # Floats, as Pinecone returns them.
    return {"source": name, "page": float(page), "chunk_index": float(index), "text": text}


def test_window_one_adds_one_chunk_on_each_side():
    assert neighbour_ids([source(7, 1)], 1) == ["a.pdf:7:0", "a.pdf:7:1", "a.pdf:7:2"]


def test_window_two_adds_two_chunks_on_each_side():
    assert neighbour_ids([source(7, 3)], 2) == ["a.pdf:7:1", "a.pdf:7:2", "a.pdf:7:3", "a.pdf:7:4", "a.pdf:7:5"]


def test_first_chunk_on_a_page_has_no_earlier_neighbour():
    assert neighbour_ids([source(7, 0)], 1) == ["a.pdf:7:0", "a.pdf:7:1"]


def test_overlapping_windows_give_no_duplicates():
    assert neighbour_ids([source(7, 1), source(7, 2)], 1) == ["a.pdf:7:0", "a.pdf:7:1", "a.pdf:7:2", "a.pdf:7:3"]


def test_join_sorts_into_reading_order_by_number_not_text():
    records = [record(7, 10, "c"), record(7, 2, "a"), record(7, 3, "b")]
    assert join_chunks(records) == "ab" + SEPARATOR + "c"


def test_next_door_chunks_join_with_no_separator():
    assert join_chunks([record(7, 0, "Week"), record(7, 1, "ly")]) == "Weekly"


def test_separator_between_gaps_pages_and_documents():
    assert join_chunks([record(7, 0, "a"), record(7, 2, "b")]) == "a" + SEPARATOR + "b"
    assert join_chunks([record(7, 5, "a"), record(8, 0, "b")]) == "a" + SEPARATOR + "b"
    assert join_chunks([record(7, 0, "a"), record(7, 1, "b", "b.pdf")]) == "a" + SEPARATOR + "b"


def test_no_records_gives_empty_context():
    assert join_chunks([]) == ""
