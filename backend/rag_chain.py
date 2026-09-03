"""
Week 3 — RAG chain: given a student question, retrieve relevant course
chunks and generate a grounded answer.

This is imported by main.py's /chat endpoint. It can also be run directly
for quick manual testing:

    python3 rag_chain.py "What is third normal form?"
"""

import os
import sys
import pathlib

import dotenv
# pyrefly: ignore [missing-import]
import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI

# Load environment variables from backend/.env
dotenv.load_dotenv(pathlib.Path(__file__).parent / ".env")

VECTOR_STORE_DIR = pathlib.Path(__file__).parent / "vector_store"
COLLECTION_NAME = "moodlebot_course_content"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 4

SYSTEM_PROMPT = """You are MoodleBot, a course assistant for a Databases and \
Information Systems class. Answer the student's question using ONLY the \
course material provided in the context below. 

Rules:
- If the context does not contain enough information to answer, say so \
clearly instead of guessing or using outside knowledge.
- Keep answers concise and student-friendly.
- Do not fabricate facts, definitions, or examples not present in the context.
"""


class RagPipeline:
    def __init__(self):
        self._embed_model = None
        self._collection = None
        self._llm_client = None
        self.model_name = "groq/compound"

    @property
    def embed_model(self):
        if self._embed_model is None:
            self._embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        return self._embed_model

    @property
    def collection(self):
        if self._collection is None:
            if not VECTOR_STORE_DIR.exists():
                raise RuntimeError(
                    "Vector store not found. Run `python3 ingest.py` first "
                    "to build it from data/processed/."
                )
            client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))
            self._collection = client.get_collection(COLLECTION_NAME)
        return self._collection

    @property
    def llm_client(self):
        if self._llm_client is None:
            api_key = os.environ.get("GROK_API_KEY") or os.environ.get("GROQ_API_KEY")
            if not api_key or api_key == "your_grok_api_key_here":
                raise RuntimeError(
                    "GROK_API_KEY not set. Add your real key to backend/.env "
                    "(see README) before calling the RAG pipeline."
                )
            if api_key.startswith("gsk_"):
                base_url = os.environ.get("LLM_BASE_URL", "https://api.groq.com/openai/v1")
                self.model_name = os.environ.get("LLM_MODEL", "groq/compound")
            else:
                base_url = os.environ.get("LLM_BASE_URL", "https://api.x.ai/v1")
                self.model_name = os.environ.get("LLM_MODEL", "grok-2-latest")

            self._llm_client = OpenAI(api_key=api_key, base_url=base_url)
        return self._llm_client

    def retrieve(self, question: str, top_k: int = TOP_K) -> list[dict]:
        """Returns list of {text, topic, source_file, distance}."""
        query_embedding = self.embed_model.encode([question]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
        )
        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        ):
            chunks.append({
                "text": doc,
                "topic": meta.get("topic"),
                "source_file": meta.get("source_file"),
                "distance": dist,
            })
        return chunks

    def generate(self, question: str, retrieved_chunks: list[dict]) -> str:
        context = "\n\n---\n\n".join(
            f"[{c['topic']} / {c['source_file']}]\n{c['text']}" for c in retrieved_chunks
        )
        user_message = f"Context:\n{context}\n\nStudent question: {question}"

        response = self.llm_client.chat.completions.create(
            model=self.model_name,
            max_tokens=500,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
        return response.choices[0].message.content

    def answer(self, question: str) -> dict:
        """Full pipeline: retrieve + generate. Returns {answer, sources}."""
        chunks = self.retrieve(question)
        if not chunks:
            return {
                "answer": "I don't have any course content loaded yet to answer that. "
                          "Please check back once the knowledge base is populated.",
                "sources": [],
            }
        answer_text = self.generate(question, chunks)
        sources = sorted({f"{c['topic']}/{c['source_file']}" for c in chunks})
        return {"answer": answer_text, "sources": sources}


# Singleton used by main.py so the embedding model only loads once per process
_pipeline = None


def get_pipeline() -> RagPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = RagPipeline()
    return _pipeline


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python3 rag_chain.py "your question here"')
        sys.exit(1)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    question = " ".join(sys.argv[1:])
    pipeline = get_pipeline()
    result = pipeline.answer(question)
    print("\nAnswer:\n", result["answer"])
    print("\nSources:", result["sources"])
