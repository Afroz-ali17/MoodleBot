"""
MoodleBot backend API — skeleton for Week 2.

Week 2 goal: this just needs to run and respond to health checks.
The /chat endpoint is stubbed out; RAG wiring happens in Weeks 3-4.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="MoodleBot API", version="0.1.0")


class ChatRequest(BaseModel):
    student_id: str
    question: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    timestamp: str


@app.get("/health")
def health():
    """Used to confirm the API is up — check this after `docker compose up`
    and after running `uvicorn main:app --reload`."""
    return {"status": "ok", "service": "moodlebot-api", "time": datetime.utcnow().isoformat()}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    STUB for Week 2 — returns a placeholder so the Moodle integration
    team can build against a stable contract before RAG is wired in.

    Weeks 3-4: replace this body with:
      1. embed(req.question)
      2. retrieve top-k chunks from vector store
      3. call LLM with retrieved context
      4. log the interaction (see data/processed/interaction_log.csv)
    """
    return ChatResponse(
        answer=f"[stub] MoodleBot received: '{req.question}'. RAG pipeline not wired in yet.",
        sources=[],
        timestamp=datetime.utcnow().isoformat(),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
