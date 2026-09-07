"""
Week 3 — Ingestion pipeline: processed text -> chunks -> embeddings -> vector store.

Run this any time data/processed/ changes (new content added, or content edited):

    python3 ingest.py

It reads every .txt file under data/processed/<topic>/, splits it into
overlapping chunks, embeds each chunk, and stores it in a local Chroma
vector store at backend/vector_store/.

Chunking uses simple word-count windows with overlap — good enough for
lecture notes/slides. If retrieval quality is poor in Week 4 testing,
this is the first thing to tune (try smaller chunks for dense definition
lists, larger chunks for narrative content).
"""

import os
import sys
import pathlib
import uuid

# Disable ChromaDB telemetry to prevent network hanging
os.environ["ANONYMIZED_TELEMETRY"] = "False"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import chromadb
from sentence_transformers import SentenceTransformer

PROCESSED_DIR = pathlib.Path(__file__).parent.parent / "data" / "processed"
VECTOR_STORE_DIR = pathlib.Path(__file__).parent / "vector_store"

CHUNK_SIZE_WORDS = 200
CHUNK_OVERLAP_WORDS = 40
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # small, fast, good baseline for course text
COLLECTION_NAME = "moodlebot_course_content"


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into overlapping word-count windows."""
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end >= len(words):
            break
        start = end - overlap
    return chunks


def load_processed_documents() -> list[dict]:
    """Returns list of {text, topic, source_file} for every processed .txt file."""
    docs = []
    if not PROCESSED_DIR.exists():
        return docs
    for topic_dir in sorted(PROCESSED_DIR.iterdir()):
        if not topic_dir.is_dir():
            continue
        for txt_file in sorted(topic_dir.glob("*.txt")):
            text = txt_file.read_text(encoding="utf-8")
            docs.append({
                "text": text,
                "topic": topic_dir.name,
                "source_file": txt_file.name,
            })
    return docs


def main():
    docs = load_processed_documents()
    if not docs:
        print(f"No processed documents found in {PROCESSED_DIR}.")
        print("Run prepare_data.py first (Week 2 step) to populate data/processed/.")
        return

    try:
        model = SentenceTransformer(EMBEDDING_MODEL_NAME, local_files_only=True)
    except Exception:
        model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(VECTOR_STORE_DIR))

    # Fresh collection each run — simplest way to avoid stale/duplicate chunks
    # during Week 3-4 iteration. Switch to incremental upserts later if the
    # corpus gets large enough that full re-embedding becomes slow.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    all_chunks, all_metadatas, all_ids = [], [], []
    for doc in docs:
        chunks = chunk_text(doc["text"], CHUNK_SIZE_WORDS, CHUNK_OVERLAP_WORDS)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_metadatas.append({
                "topic": doc["topic"],
                "source_file": doc["source_file"],
                "chunk_index": i,
            })
            all_ids.append(str(uuid.uuid4()))
        print(f"  {doc['source_file']} ({doc['topic']}): {len(chunks)} chunk(s)")

    if not all_chunks:
        print("No chunks produced — check that processed .txt files aren't empty.")
        return

    print(f"\nEmbedding {len(all_chunks)} chunks...")
    embeddings = model.encode(all_chunks, show_progress_bar=True).tolist()

    collection.add(
        ids=all_ids,
        embeddings=embeddings,
        documents=all_chunks,
        metadatas=all_metadatas,
    )

    print(f"\nDone. Vector store written to {VECTOR_STORE_DIR}")
    print(f"Collection '{COLLECTION_NAME}' contains {collection.count()} chunks.")


if __name__ == "__main__":
    main()
