# MoodleBot

An LLM-driven RAG chatbot integrated into Moodle for the Databases and Information
Systems course. Final year project — Department of CSE (AI & ML), RGMCET.

## Team

| Member | Roll No. | Track |
|---|---|---|
| M. Sumanth | 23091A3351 | RAG pipeline / backend |
| P. Umesh | 23091A3359 | Moodle integration |
| P. Afroz Ali Khan | 24095A3301 | Data / evaluation / TAM |

Guide: Dr. G. Kishor Kumar, Professor, Dept. of CSE (AI & ML), RGMCET

## Project structure

```
moodlebot/
├── docker-compose.yml       # Moodle + MySQL, runs locally
├── backend/
│   ├── main.py               # FastAPI app (chat endpoint, health check)
│   ├── prepare_data.py       # Converts raw course materials -> clean text
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

## Environment variables (needed from Week 3 onward)

Create `backend/.env` (not committed to git) with:
```
ANTHROPIC_API_KEY=your_key_here
# or OPENAI_API_KEY=your_key_here
```

## Roadmap

See `docs/` for the full 10-week plan and requirements documents.
