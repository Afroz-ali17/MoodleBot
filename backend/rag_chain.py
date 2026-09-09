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

SYSTEM_PROMPT = """You are MoodleBot, the intelligent academic AI Teaching Assistant \
for RGMCET, supporting students across the entire engineering and computer science curriculum \
(including Programming in Python & Java, Data Structures & Algorithms, Natural Language Processing, \
Computer Vision, Big Data & Analytics, Database Systems, Mathematics, Quantum Technologies, and RPA). \
Answer the student's question accurately and clearly using ONLY the provided course material in the context below.

Guidelines:
1. Grounding: Rely strictly on the provided course context. Do not fabricate or assume outside facts.
2. Structure: Format answers clearly with bold key concepts, bullet points, syntax blocks, or comparison tables where appropriate.
3. Multi-Subject Context: Ensure definitions and explanations directly reflect the relevant subject's lecture notes and slides.
4. Transparency: If a specific detail (e.g. edge-case code or extended theoretical formula) is not present in the course text, clearly state what the course notes confirm.
"""


class RagPipeline:
    def __init__(self):
        self._embed_model = None
        self._collection = None
        self._llm_client = None
        self.model_name = "qwen/qwen3.8-27b"

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

    def retrieve(self, question: str, top_k: int = TOP_K, subject: str | None = None) -> list[dict]:
        """
        Returns list of {text, topic, source_file, distance}.
        If subject is specified, filters strictly to that course module.
        Otherwise, conducts universal semantic search across all 18 curriculum subjects.
        """
        query_embedding = self.embed_model.encode([question]).tolist()
        query_kwargs = {
            "query_embeddings": query_embedding,
            "n_results": top_k,
        }
        if subject and subject.strip() and subject.lower() not in ("all", "any"):
            query_kwargs["where"] = {"topic": subject.strip().lower()}

        results = self.collection.query(**query_kwargs)
        chunks = []
        if results and results["documents"] and results["documents"][0]:
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

    def answer(self, question: str, subject: str | None = None) -> dict:
        """Full pipeline: retrieve + generate across all subjects or a specific course."""
        chunks = self.retrieve(question, subject=subject)
        if not chunks:
            subj_desc = f" for subject '{subject}'" if subject else ""
            return {
                "answer": f"I don't have relevant course content{subj_desc} to answer that question. "
                          "Please verify the subject or check back once additional materials are loaded.",
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
        print('Usage: python3 rag_chain.py "your question here" [--subject <topic_slug>]')
        sys.exit(1)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    
    subject = None
    args = sys.argv[1:]
    if "--subject" in args:
        idx = args.index("--subject")
        if idx + 1 < len(args):
            subject = args[idx + 1]
            args = args[:idx] + args[idx + 2:]
    
    question = " ".join(args)
    pipeline = get_pipeline()
    result = pipeline.answer(question, subject=subject)
    print(f"\n[Subject: {subject or 'All Subjects'}]")
    print("\nAnswer:\n", result["answer"])
    print("\nSources:", result["sources"])
