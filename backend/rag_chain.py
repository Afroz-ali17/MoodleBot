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

# Disable ChromaDB telemetry to prevent hanging on network drops
os.environ["ANONYMIZED_TELEMETRY"] = "False"

# Load environment variables from backend/.env
dotenv.load_dotenv(pathlib.Path(__file__).parent / ".env")

VECTOR_STORE_DIR = pathlib.Path(__file__).parent / "vector_store"
COLLECTION_NAME = "moodlebot_course_content"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 4

DBMS_CORE_TOPICS = {
    "dbms",
    "introduction-dbms",
    "er-diagrams",
    "relational-algebra",
    "normalization",
    "transactions",
}

SYSTEM_PROMPT = """You are MoodleBot, the AI teaching assistant for the Database \
Management Systems course. Answer the student's question using ONLY the provided course context.

Guidelines:
1. Grounding: Rely strictly on the provided context. Do not invent or assume outside facts.
2. Structure: Format answers clearly using bold key terms, bullet points, or comparison tables.
3. Completeness: Thoroughly explain definitions, distinctions, and properties present in the text.
4. Transparency: If a specific detail (e.g. syntax or extended diagram) is omitted in the course text, clearly state what the course slides confirm.
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
            try:
                # Prefer local cache to avoid HuggingFace network latency / DNS drops
                self._embed_model = SentenceTransformer(
                    EMBEDDING_MODEL_NAME, local_files_only=True
                )
            except Exception:
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
                self.model_name = os.environ.get("LLM_MODEL", "qwen/qwen3.8-27b")
            else:
                base_url = os.environ.get("LLM_BASE_URL", "https://api.x.ai/v1")
                self.model_name = os.environ.get("LLM_MODEL", "grok-2-latest")

            self._llm_client = OpenAI(api_key=api_key, base_url=base_url, timeout=25.0)
        return self._llm_client

    def retrieve(self, question: str, top_k: int = TOP_K) -> list[dict]:
        """Returns list of {text, topic, source_file, distance}, prioritizing core DBMS modules."""
        query_embedding = self.embed_model.encode([question]).tolist()
        candidates_k = min(top_k * 2, 10)
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=candidates_k,
        )
        candidates = []
        for doc, meta, dist in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        ):
            candidates.append({
                "text": doc,
                "topic": meta.get("topic"),
                "source_file": meta.get("source_file"),
                "distance": dist,
            })

        # Prioritize core DBMS topics over elective courses
        def priority_score(c):
            is_core = 0 if c["topic"] in DBMS_CORE_TOPICS else 1
            return (is_core, c["distance"])

        candidates.sort(key=priority_score)
        return candidates[:top_k]

    def generate(self, question: str, retrieved_chunks: list[dict]) -> str:
        context = "\n\n---\n\n".join(
            f"[{c['topic']} / {c['source_file']}]\n{c['text']}" for c in retrieved_chunks
        )
        user_message = f"Context:\n{context}\n\nStudent question: {question}"

        try:
            response = self.llm_client.chat.completions.create(
                model=self.model_name,
                max_tokens=350,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            if "413" in str(e) or "too large" in str(e).lower():
                short_context = "\n\n---\n\n".join(
                    f"[{c['topic']} / {c['source_file']}]\n{c['text'][:800]}" for c in retrieved_chunks[:2]
                )
                user_msg_short = f"Context:\n{short_context}\n\nStudent question: {question}"
                response = self.llm_client.chat.completions.create(
                    model=self.model_name,
                    max_tokens=250,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_msg_short},
                    ],
                )
                return response.choices[0].message.content
            raise

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
