"""
MoodleBot backend API.

Week 3 update: /chat now runs the real RAG pipeline (retrieval + grounded
generation) instead of returning a stub. Requires:
  1. backend/vector_store/ to exist (run ingest.py first)
  2. GROK_API_KEY set in backend/.env
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime

from rag_chain import get_pipeline

app = FastAPI(title="MoodleBot API", version="0.2.0")


class ChatRequest(BaseModel):
    student_id: str
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    timestamp: str


import pathlib
from fastapi.responses import FileResponse

STATIC_DIR = pathlib.Path(__file__).parent / "static"


@app.get("/")
def root():
    """Serves the interactive MoodleBot Web Interface."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "message": "Welcome to MoodleBot API",
        "version": "0.2.0",
        "docs": "/docs",
        "health": "/health",
        "chat": "/chat"
    }


@app.get("/health")
def health():
    """Used to confirm the API is up — check this after `docker compose up`
    and after running `uvicorn main:app --reload`."""
    return {"status": "ok", "service": "moodlebot-api", "time": datetime.utcnow().isoformat()}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Runs the RAG pipeline: retrieve relevant course chunks, then generate
    a grounded answer from the LLM.

    Interaction logging (for Week 12-13 accuracy evaluation) gets added
    once the pilot deployment step is closer — tracked as a Week 4 TODO.
    """
    try:
        pipeline = get_pipeline()
        result = pipeline.answer(req.question)
    except RuntimeError as e:
        # Expected setup issues: vector store missing (run ingest.py) or API key missing
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        # Unexpected failures (network errors, model download issues, LLM API
        # errors, etc.) — surfaced as 502 rather than crashing the request.
        raise HTTPException(status_code=502, detail=f"RAG pipeline error: {e}")

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        timestamp=datetime.utcnow().isoformat(),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
