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

## Week 4 — test and refine the RAG pipeline

Manual spot-checks in Week 3 tell you if things basically work. Week 4 is
about measuring accuracy systematically and tuning based on real numbers —
this is also where your abstract's 88% accuracy figure will come from.

### 1. Build a real test question set

Expand `backend/test_questions.csv` (a template with 8 sample rows is
included) into at least 15-30 questions that cover every topic in your
course. Columns:
- `topic` — should match your `data/raw/` topic-slug naming
- `question` — a realistic student question
- `expected_answer_notes` — what a correct answer should mention (used for
  your own grading, not by the script)

### 2. Run the evaluation harness

```bash
cd backend
python3 evaluate.py
```

This runs every question through your live RAG pipeline and writes
`results/eval_<timestamp>.csv` with each generated answer, which sources
were retrieved, and response time. Errors on individual questions are
caught and logged per-row — one bad question won't kill the whole run.

### 3. Grade the results by hand

Open the results CSV and fill in `human_verdict` for every row:
- `correct` — accurate and grounded in course content
- `partial` — mostly right but incomplete or slightly off
- `incorrect` — wrong, hallucinated, or off-topic

Add a short note in `human_notes` for anything that went wrong — this is
what tells you *what* to fix, not just the score.

### 4. Score it

```bash
python3 score.py results/eval_<timestamp>.csv
```

This prints strict accuracy (correct-only), lenient accuracy (partial =
half credit), and a per-topic breakdown so you can see exactly where
weaknesses are concentrated.

### 5. Tune and re-run

If accuracy is below your target:
| Symptom | Likely cause | Try |
|---|---|---|
| Wrong topic retrieved | Chunks too broad/narrow, or `TOP_K` too low | Adjust `CHUNK_SIZE_WORDS`/`CHUNK_OVERLAP_WORDS` in `ingest.py`, or `TOP_K` in `rag_chain.py` |
| Right chunks, wrong/vague answer | Prompt not strict enough | Tighten `SYSTEM_PROMPT` in `rag_chain.py` |
| Hallucinated details | Model ignoring "use only context" instruction | Make the system prompt more explicit; consider lowering `max_tokens` |
| Slow responses | Too many/too-large retrieved chunks | Lower `TOP_K` or `CHUNK_SIZE_WORDS` |

After any change to chunking, re-run `python3 ingest.py` to rebuild the
vector store, then re-run `evaluate.py` + `score.py` to compare against
your previous run. Keep every dated results CSV — this run history is
useful evidence for your final report.

**Target for end of Week 4:** a documented accuracy score (aim for 88%+ to
match your abstract's benchmark) across a real, multi-topic test set, with
at least one tuning iteration showing before/after improvement.

## Roadmap

See `docs/` for the full 10-week plan and requirements documents.
