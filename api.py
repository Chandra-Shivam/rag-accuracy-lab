"""SERVING box of MAP.md: HTTP API over answer() and stream_answer().

Usage: uvicorn api:api --reload
POST /ask         {"question": "..."} -> JSON with answer, sources and citations
POST /ask/stream  same body -> server-sent events: sources, then token (many), then done (citations)
GET /             -> the chat page (static/index.html)
Needs GOOGLE_API_KEY and PINECONE_API_KEY in .env.
"""

import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from corpus.download import sources as corpus_sources
from rag.answer import answer, stream_answer

api = FastAPI()
URLS = {filename: url for filename, url, _ in corpus_sources()}


def with_urls(sources):
    """Adds each source's IRS link; #page=N opens the PDF at that page."""
    return [{**s, "url": f"{URLS[s['source']]}#page={s['page']}"} for s in sources]


class AskRequest(BaseModel):
    question: str


@api.post("/ask")
def query(request: AskRequest):
    """Returns the whole answer at once."""
    response = answer(request.question)
    return {"answer": response["answer"], "sources": with_urls(response["sources"]), "citations": response["citations"]}


@api.post("/ask/stream")
def query_stream(request: AskRequest):
    """Sends the answer as it is generated, as server-sent events."""
    def events():
        for event, data in stream_answer(request.question):
            if event == "sources":
                data = with_urls(data)
            yield f"event: {event}\ndata: {json.dumps(data)}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream")


@api.get("/")
def page():
    """Serves the chat page."""
    return FileResponse(Path(__file__).parent / "static" / "index.html")