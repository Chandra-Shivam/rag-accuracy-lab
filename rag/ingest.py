"""INDEXING, first two boxes of MAP.md: load pages -> chunk (naive v0).

Usage: python -m rag.ingest   (prints corpus and chunk counts)
"""
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

CORPUS = Path(__file__).resolve().parent.parent / "corpus"
CHUNK_SIZE = 1000  # characters; v0 has no overlap and no structure awareness


def load_pages(corpus=CORPUS):
    """One Document per PDF page, with metadata {source, page}."""
    pages = []
    for path in sorted(Path(corpus).glob("*.pdf")):
        for doc in PyPDFLoader(str(path)).load():
            # PyPDFLoader counts pages from 0; the golden set uses the 1-based file page index.
            # Convert here and nowhere else. Never use metadata["page_label"] (the printed number).
            page = doc.metadata["page"] + 1
            pages.append(Document(page_content=doc.page_content, metadata={"source": path.name, "page": page}))
    return pages


def chunk_pages(pages, size=CHUNK_SIZE):
    """Slice each page into fixed-size pieces; chunks never cross a page boundary."""
    chunks = []
    for page in pages:
        text = page.page_content
        for index, start in enumerate(range(0, len(text), size)):
            metadata = {**page.metadata, "chunk_index": index}
            chunks.append(
                Document(
                    id=f"{metadata['source']}:{metadata['page']}:{index}",
                    page_content=text[start : start + size],
                    metadata=metadata,
                )
            )
    return chunks


if __name__ == "__main__":
    pages = load_pages()
    chunks = chunk_pages(pages)
    empty = [f"{p.metadata['source']}:{p.metadata['page']}" for p in pages if not p.page_content.strip()]
    print(f"{len(pages)} pages, {len(chunks)} chunks, {len(empty)} empty pages {empty}")
    print(f"page numbers range {min(p.metadata['page'] for p in pages)}..{max(p.metadata['page'] for p in pages)}")
