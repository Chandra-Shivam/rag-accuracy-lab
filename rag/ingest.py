"""INDEXING, first two boxes of MAP.md: load pages -> chunk (naive v0).

Usage: python -m rag.ingest          (prints corpus and chunk counts)
       python -m rag.ingest --save   (same, and writes the chunk file without re-indexing Pinecone)
       CLEAN=before python -m rag.store    (indexes chunks cut after removing the print-proof header)
       CLEAN=after python -m rag.store     (same cuts as today, with the header removed from the chunks)
"""
import json
import os
import re
import sys
from pathlib import Path

from langchain_core.documents import Document

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
CHUNK_SIZE = 1000  # characters; v0 has no overlap and no structure awareness
# IRS print-proof text: "Userid: ..." on first pages, "Page N of M  Fileid: ..." on the rest (mid-page in p509).
PROOF_HEADER = re.compile(r"(?:Userid: |Page \d+ of \d+\s+Fileid: ).*?MUST be removed before printing\.\s*", re.DOTALL)
CLEAN = os.environ.get("CLEAN")  # None, "before" or "after": when the header is removed, relative to cutting
# Written with the Pinecone index and read by BM25 at startup, so serving needs no PDFs.
# Different chunks get their own file, as they get their own index.
CHUNKS_FILE = ROOT / "data" / (f"chunks-clean-{CLEAN}.jsonl" if CLEAN else "chunks.jsonl")


def load_pages(corpus=CORPUS):
    """One Document per PDF page, with metadata {source, page}."""
    # Imported here so that serving, which reads the chunk file, doesn't need the PDF loader.
    from langchain_community.document_loaders import PyPDFLoader

    pages = []
    for path in sorted(Path(corpus).glob("*.pdf")):
        for doc in PyPDFLoader(str(path)).load():
            # PyPDFLoader counts pages from 0; the golden set uses the 1-based file page index.
            # Convert here and nowhere else. Never use metadata["page_label"] (the printed number).
            page = doc.metadata["page"] + 1
            pages.append(Document(page_content=doc.page_content, metadata={"source": path.name, "page": page}))
    return pages


def clean_page(text):
    """Removes the print-proof header; pages without one are returned unchanged."""
    return PROOF_HEADER.sub("", text, count=1)


def _remove_span(text, offset, span):
    # Keeps the characters of a piece that started at offset, except those inside span.
    return "".join(char for position, char in enumerate(text, offset) if not span[0] <= position < span[1])


def chunk_pages(pages, size=CHUNK_SIZE, clean=CLEAN):
    """Slice each page into fixed-size pieces; chunks never cross a page boundary."""
    chunks = []
    for page in pages:
        text = clean_page(page.page_content) if clean == "before" else page.page_content
        # "after" keeps every cut where it is today, so only the header's own characters change.
        header = PROOF_HEADER.search(text) if clean == "after" else None
        for index, start in enumerate(range(0, len(text), size)):
            piece = text[start : start + size]
            if header:
                piece = _remove_span(piece, start, header.span())
            metadata = {**page.metadata, "chunk_index": index}
            chunks.append(
                Document(
                    id=f"{metadata['source']}:{metadata['page']}:{index}",
                    page_content=piece,
                    metadata=metadata,
                )
            )
    return chunks


def save_chunks(chunks, path=CHUNKS_FILE):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps({"id": c.id, "text": c.page_content, "metadata": c.metadata}) + "\n"
                            for c in chunks))


def load_chunks(path=CHUNKS_FILE):
    # No fallback to the PDFs: a quiet rebuild could hide chunks that no longer match the Pinecone index.
    if not path.exists():
        raise FileNotFoundError(f"no chunk file at {path}: run python -m rag.ingest --save")
    return [Document(id=row["id"], page_content=row["text"], metadata=row["metadata"])
            for row in map(json.loads, path.read_text().splitlines())]


if __name__ == "__main__":
    pages = load_pages()
    chunks = chunk_pages(pages)
    empty = [f"{p.metadata['source']}:{p.metadata['page']}" for p in pages if not p.page_content.strip()]
    print(f"{len(pages)} pages, {len(chunks)} chunks, {len(empty)} empty pages {empty}")
    print(f"page numbers range {min(p.metadata['page'] for p in pages)}..{max(p.metadata['page'] for p in pages)}")
    if "--save" in sys.argv:
        save_chunks(chunks)
        print(f"saved {len(chunks)} chunks to {CHUNKS_FILE}")
