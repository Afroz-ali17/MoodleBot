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
    subject: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[str] = []
    subject: str | None = None
    timestamp: str


import pathlib
from fastapi.responses import FileResponse

STATIC_DIR = pathlib.Path(__file__).parent / "static"
PROCESSED_DIR = pathlib.Path(__file__).parent.parent / "data" / "processed"


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
    pipeline = get_pipeline()
    total_chunks = pipeline.collection.count() if pipeline.collection else 0
    return {
        "status": "ok",
        "service": "moodlebot-multi-subject-api",
        "total_chunks": total_chunks,
        "model": pipeline.model_name,
        "time": datetime.utcnow().isoformat()
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


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Runs the multi-subject RAG pipeline: retrieves relevant course chunks
    (with optional subject filtering) and generates a grounded response.
    """
    try:
        pipeline = get_pipeline()
        result = pipeline.answer(req.question, subject=req.subject)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"RAG pipeline error: {e}")

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        subject=req.subject or "All Subjects",
        timestamp=datetime.utcnow().isoformat(),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
