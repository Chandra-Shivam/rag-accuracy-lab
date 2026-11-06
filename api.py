"""SERVING box of MAP.md: HTTP API over answer() and stream_answer().

Usage: uvicorn api:api --reload
POST /ask         {"question": "..."} -> JSON with answer, sources and citations
POST /ask/stream  same body -> server-sent events: sources, then token (many), then done (citations)
Needs GOOGLE_API_KEY and PINECONE_API_KEY in .env.
"""

import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from rag.answer import answer, stream_answer

api = FastAPI()


class AskRequest(BaseModel):
    question: str


@api.post("/ask")
def query(request: AskRequest):
    """Returns the whole answer at once."""
    response = answer(request.question)
    return {"answer": response["answer"], "sources": response["sources"], "citations": response["citations"]}


@api.post("/ask/stream")
def query_stream(request: AskRequest):
    """Sends the answer as it is generated, as server-sent events."""
    def events():
        for event, data in stream_answer(request.question):
            yield f"event: {event}\ndata: {json.dumps(data)}\n\n"
    return StreamingResponse(events(), media_type="text/event-stream")