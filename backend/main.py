"""
MoodleBot backend API.

Week 5 update:
  - Database persistence via SQLite (db.py)
  - Multi-turn conversation sessions & history
  - Salted hash for student privacy (NFR-6)
  - Feedback rating endpoint (/feedback)
  - History retrieval endpoint (/history/{session_id})
  - API Key protection (MOODLEBOT_API_KEY / X-API-Key)
  - Rate limiting (RATE_LIMIT_PER_MIN)
  - Input validation (Pydantic schema constraints)
"""

import collections
import hashlib
import os
import pathlib
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator

import db
from rag_chain import get_pipeline

STATIC_DIR = pathlib.Path(__file__).parent / "static"
PROCESSED_DIR = pathlib.Path(__file__).parent.parent / "data" / "processed"
SALT = os.environ.get("ANON_SALT") or os.environ.get("MOODLEBOT_SALT", "moodlebot-secret-salt-2026")
SESSION_ID_PATTERN = r"^[a-zA-Z0-9_-]{1,64}$"

_rate_limits: dict[str, list[float]] = collections.defaultdict(list)


def hash_student(student_id: str) -> str:
    """Salted SHA-256 hash truncated to 32 hex chars for student privacy."""
    return hashlib.sha256(f"{SALT}:{student_id}".encode()).hexdigest()[:32]


def _get_pipeline():
    """Returns the RAG pipeline singleton (mockable in unit tests)."""
    return get_pipeline()


def verify_api_key(x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None):
    required_key = os.environ.get("MOODLEBOT_API_KEY")
    if required_key:
        if not x_api_key or x_api_key != required_key:
            raise HTTPException(status_code=401, detail="Unauthorized: invalid or missing API key")


def check_rate_limit(student_id: str):
    limit_str = os.environ.get("RATE_LIMIT_PER_MIN", "60")
    try:
        limit = int(limit_str)
    except ValueError:
        limit = 60
    now = time.time()
    window = 60.0
    timestamps = _rate_limits[student_id]
    _rate_limits[student_id] = [t for t in timestamps if now - t < window]
    if len(_rate_limits[student_id]) >= limit:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again shortly.")
    _rate_limits[student_id].append(now)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    if not os.environ.get("MOODLEBOT_SKIP_WARMUP"):
        try:
            _get_pipeline().warmup()
        except Exception:
            pass
    yield


# Initialize SQLite schema
db.init_db()

app = FastAPI(title="MoodleBot API", version="0.3.0", lifespan=lifespan)


class ChatRequest(BaseModel):
    student_id: str = Field(..., min_length=1)
    question: str = Field(..., min_length=1, max_length=1000)
    subject: str | None = None
    course_id: str | None = None
    session_id: str | None = Field(None, pattern=SESSION_ID_PATTERN)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    session_id: str
    interaction_id: int
    subject: str | None = None
    course_id: str | None = None
    timestamp: str


class FeedbackRequest(BaseModel):
    student_id: str = Field(..., min_length=1)
    interaction_id: int
    rating: int = Field(..., description="1 for helpful, -1 for not helpful")
    comment: str | None = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: int):
        if v not in (1, -1):
            raise ValueError("Rating must be either 1 or -1")
        return v


@app.get("/")
def root():
    """Serves the interactive MoodleBot Web Interface."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "message": "Welcome to MoodleBot Universal Academic Assistant API",
        "version": "0.3.0",
        "docs": "/docs",
        "health": "/health",
        "subjects": "/subjects",
        "chat": "/chat"
    }


@app.get("/health")
def health():
    """Confirms API status and loaded vector knowledge base."""
    total_chunks = 0
    model_name = "unknown"
    vector_store_ready = False
    try:
        pipeline = _get_pipeline()
        if hasattr(pipeline, "collection") and pipeline.collection:
            total_chunks = pipeline.collection.count()
            vector_store_ready = total_chunks > 0
        if hasattr(pipeline, "model_name"):
            model_name = pipeline.model_name
    except Exception:
        pass
    return {
        "status": "ok",
        "service": "moodlebot-multi-subject-api",
        "total_chunks": total_chunks,
        "vector_store_ready": vector_store_ready,
        "auth_enabled": bool(os.environ.get("MOODLEBOT_API_KEY")),
        "model": model_name,
        "time": datetime.now(timezone.utc).isoformat()
    }


@app.get("/subjects")
def get_subjects():
    """Returns all 18 academic subject categories indexed in the knowledge base."""
    subjects = [
        {"slug": "python", "name": "Python Programming", "category": "Programming"},
        {"slug": "java", "name": "Java & Object-Oriented Programming", "category": "Programming"},
        {"slug": "adsa", "name": "Advanced Data Structures & Algorithms", "category": "Programming"},
        {"slug": "nlp", "name": "Natural Language Processing (NLP)", "category": "AI & Analytics"},
        {"slug": "computer-vision-and-image-processing", "name": "Computer Vision & Image Processing", "category": "AI & Analytics"},
        {"slug": "big-data-and-analysis", "name": "Big Data & Analysis", "category": "AI & Analytics"},
        {"slug": "exploratort-data-analysis", "name": "Exploratory Data Analysis (EDA)", "category": "AI & Analytics"},
        {"slug": "dbms", "name": "Database Management Systems (Units 1-5)", "category": "Databases"},
        {"slug": "introduction-dbms", "name": "DBMS Overview & 3-Tier Architecture", "category": "Databases"},
        {"slug": "er-diagrams", "name": "ER Modeling & Relational Constraints", "category": "Databases"},
        {"slug": "relational-algebra", "name": "Relational Algebra & SQL", "category": "Databases"},
        {"slug": "normalization", "name": "Database Normalization (1NF-BCNF)", "category": "Databases"},
        {"slug": "transactions", "name": "Transactions, Concurrency & ACID", "category": "Databases"},
        {"slug": "iqta", "name": "Quantum Theory & Technologies", "category": "Advanced Tech"},
        {"slug": "rpa", "name": "Robotic Process Automation (RPA)", "category": "Advanced Tech"},
        {"slug": "opitimization-techniques", "name": "Optimization Techniques", "category": "Mathematics"},
        {"slug": "dmgt", "name": "Discrete Mathematics & Graph Theory", "category": "Mathematics"},
        {"slug": "academic-writing-and-public-speaking", "name": "Academic Writing & Public Speaking", "category": "Professional"}
    ]
    return {"total": len(subjects), "subjects": subjects}


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)])
def chat(req: ChatRequest):
    """
    Runs the multi-subject RAG pipeline: retrieves relevant course chunks
    (with optional subject filtering) and generates a grounded response.
    """
    check_rate_limit(req.student_id)
    student_hash = hash_student(req.student_id)
    session_id = req.session_id or uuid.uuid4().hex[:16]

    # Conversation history for this session & student
    history = db.get_history(session_id, student_hash)

    t0 = time.time()
    try:
        pipeline = _get_pipeline()
        try:
            result = pipeline.answer(req.question, history=history, subject=req.subject)
        except TypeError:
            result = pipeline.answer(req.question, history=history)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"RAG pipeline error: {e}")
    elapsed = time.time() - t0

    interaction_id = db.log_interaction(
        session_id=session_id,
        student_hash=student_hash,
        course_id=req.course_id,
        question=req.question,
        answer=result["answer"],
        sources=result["sources"],
        response_time_s=elapsed,
    )

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        session_id=session_id,
        interaction_id=interaction_id,
        subject=req.subject or "All Subjects",
        course_id=req.course_id,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/history/{session_id}", dependencies=[Depends(verify_api_key)])
def get_session_history(session_id: str, student_id: str = Query(...)):
    """Returns conversation transcript of a session, scoped to the verified student."""
    student_hash = hash_student(student_id)
    messages = db.get_session_transcript(session_id, student_hash)
    return {
        "session_id": session_id,
        "messages": messages,
    }


@app.post("/feedback", dependencies=[Depends(verify_api_key)])
def submit_feedback(req: FeedbackRequest):
    """Logs student rating (+1 helpful / -1 unhelpful) on a chatbot response."""
    student_hash = hash_student(req.student_id)
    ok = db.set_feedback(req.interaction_id, student_hash, req.rating, req.comment)
    if not ok:
        raise HTTPException(status_code=404, detail="Interaction not found or does not belong to student")
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
