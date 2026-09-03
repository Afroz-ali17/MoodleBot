# MoodleBot

An LLM-driven RAG chatbot integrated into Moodle for the Databases and Information
Systems course. Final year project — Department of CSE (AI & ML), RGMCET.

## Team

| Member | Roll No. | 
|---|---|---|
| M. Sumanth | 23091A3351 |
| P. Umesh | 23091A3359 | 
| P. Afroz Ali Khan | 24095A3301 |

Guide: Dr. G. Kishor Kumar, Professor, Dept. of CSE (AI & ML), RGMCET

## Project structure

```
moodlebot/
├── docker-compose.yml       # Moodle + MySQL, runs locally
├── backend/
│   ├── main.py               # FastAPI app (chat endpoint, health check)
│   ├── prepare_data.py       # Week 2: converts raw course materials -> clean text
│   ├── ingest.py              # Week 3: chunks processed text -> embeddings -> vector store
│   ├── rag_chain.py           # Week 3: retrieval + grounded LLM generation
│   ├── vector_store/          # Created by ingest.py — gitignored, rebuild locally
│   ├── .env.example
│   └── requirements.txt
├── data/
│   ├── raw/                  # Drop PDFs/PPTX/DOCX course materials here
│   └── processed/            # Cleaned .txt output + manifest.csv
├── moodle-plugin/            # Moodle chat widget/plugin (Week 5+)
└── docs/                     # Diagrams, reports, planning docs
```

## Week 2 setup — do this today

### 1. Start Moodle

```bash
docker compose up -d
```

Wait ~2-3 minutes for first boot, then visit **http://localhost:8080**.
Login: `admin` / `ChangeMe123!` (change this before any real deployment).

Check container health any time with:
```bash
docker compose ps
```

### 2. Set up the backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Run the API:
```bash
uvicorn main:app --reload
```

Confirm it's alive:
```bash
curl http://localhost:8000/health
```

You should see `{"status":"ok", ...}`. The `/chat` endpoint currently returns
a stub response — that's expected until the RAG pipeline is wired in during
Weeks 3-4.

### 3. Collect course data

Drop raw files into `data/raw/` using this naming convention so content gets
auto-tagged by topic:

```
<topic-slug>__<original-filename>.pdf
```

Example: `normalization__week4_notes.pdf`, `er-diagrams__lecture3.pptx`

Then run:
```bash
cd backend
python3 prepare_data.py
```

This produces cleaned `.txt` files under `data/processed/<topic>/` plus a
`manifest.csv` index — check the word counts in there to make sure nothing
extracted as empty/garbled.

**Target for end of Week 2:** every syllabus/notes/slide/FAQ file for the
target course is in `data/raw/`, and `prepare_data.py` has run clean with no
extraction failures.

## Week 3 — build the RAG pipeline

### 1. Set your API key

```bash
cp backend/.env.example backend/.env
# edit backend/.env and paste in your real GROK_API_KEY
```

Then load it before running anything (or use `python-dotenv` — already in
requirements.txt, just make sure `main.py`/`rag_chain.py` load it — see note
below if you haven't wired that up yet):

```bash
export $(cat backend/.env | xargs)   # macOS/Linux
```

### 2. Build the vector store

Make sure `data/processed/` is populated (Week 2 step — run `prepare_data.py`
if you haven't). Then:

```bash
cd backend
python3 ingest.py
```

First run downloads the embedding model (`all-MiniLM-L6-v2`, ~90MB) — this
needs a real internet connection. You'll see per-file chunk counts, then a
confirmation that the vector store was written to `backend/vector_store/`.

**Re-run this any time you add or change course content.**

### 3. Test retrieval + generation directly

Before going through the API, sanity-check the pipeline on its own:

```bash
python3 rag_chain.py "What is third normal form?"
```

You should get back an answer grounded in your course content, plus a list
of source files it pulled from. If the answer looks wrong or ungrounded,
that's a signal to revisit chunk size/overlap in `ingest.py` (Week 4 tuning).

### 4. Test through the full API

```bash
uvicorn main:app --reload
```

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"student_id": "test1", "question": "What is 3NF?"}'
```

**Common errors and what they mean:**
| Error | Cause | Fix |
|---|---|---|
| `503 Vector store not found` | `ingest.py` hasn't been run yet | Run it (step 2) |
| `503 GROK_API_KEY not set` | `.env` missing or not loaded | Check step 1 |
| `502 RAG pipeline error: ... huggingface.co ...` | No internet access, or model not cached yet | Check connection; first run needs to download the model once |

**Target for end of Week 3:** `ingest.py` runs clean over your full course
corpus, and `rag_chain.py` gives sensible, grounded answers to a handful of
manual test questions across different topics.

## Roadmap

See `docs/` for the full 10-week plan and requirements documents.
