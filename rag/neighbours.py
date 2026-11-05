"""ANSWERING box of MAP.md: small-to-big. Search finds small chunks; the LLM also gets the chunks next to them.

No Pinecone here, so tests can run without it: retrieve() in rag/answer.py does the fetch.
"""
SEPARATOR = "\n\n---\n\n"


def label(source, page):
    """The line above each context block. The model reads it to cite the document and page."""
    # Pinecone returns numbers in metadata as floats; "page 4.0" must not reach the prompt.
    return f"[{source}, page {int(page)}]\n"


def neighbour_ids(sources, window):
    """Ids of each source chunk and up to window chunks on each side, same page only.

    The last id on a page may not exist; Pinecone's fetch just leaves it out.
    """
    ids = set()
    for s in sources:
        for index in range(max(s["chunk_index"] - window, 0), s["chunk_index"] + window + 1):
            ids.add(f"{s['source']}:{s['page']}:{index}")
    return sorted(ids)


def join_chunks(records):
    """Context text from chunk metadata, in reading order. Next-door chunks join with no separator.

    Chunks are cut at a fixed size, so a word can run across two of them.
    Each new block starts with a label; next-door chunks share the label of their block.
    """
    # Pinecone returns numbers in metadata as floats, so convert before sorting and comparing.
    rows = sorted((r["source"], int(r["page"]), int(r["chunk_index"]), r["text"]) for r in records)
    context, previous = "", None
    for source, page, index, text in rows:
        if previous == (source, page, index - 1):
            context += text
        else:
            block = label(source, page) + text
            context += block if previous is None else SEPARATOR + block
        previous = (source, page, index)
    return context
