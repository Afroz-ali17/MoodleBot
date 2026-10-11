# MoodleBot — Week 5 Comprehensive Progress Report
**Department of Computer Science & Engineering (AI & ML)**  
**Rajeev Gandhi Memorial College of Engineering and Technology (Autonomous), Nandyal**

---

### Project Metadata
- **Project Title:** MoodleBot — Universal Institutional AI Academic Assistant Powered by Multi-Subject RAG
- **Institution:** Rajeev Gandhi Memorial College of Engineering and Technology (RGMCET)
- **Project Guide:** Dr. G. Kishor Kumar, Professor, Dept. of CSE (AI & ML), RGMCET
- **Team Members:**
  - M. Sumanth (23091A3351) — RAG Pipeline & Backend Architecture
  - P. Umesh (23091A3359) — Moodle LMS Integration & Docker Infrastructure
  - P. Afroz Ali Khan (24095A3301) — Data Engineering, Evaluation & TAM Framework
- **Milestone Covered:** **Week 5 — LMS Block Plugin Development, SQLite Persistence Layer, Multi-Turn Conversation History, Student Privacy & Feedback Rating**
- **Date:** October 11, 2026
- **Repository:** [https://github.com/Afroz-ali17/MoodleBot](https://github.com/Afroz-ali17/MoodleBot)

---

## 1. Executive Summary

During **Week 4**, the team benchmarked the RAG pipeline at **93.1% strict accuracy (96.6% lenient)** and expanded the system to support all 18 curriculum subjects.

In **Week 5**, our engineering focus transitioned from standalone RAG evaluation to **full LMS integration and production-grade backend persistence**:
1. **Moodle Block Plugin (`block_moodlebot`)**: Built a complete native Moodle 4.x block plugin in PHP and JavaScript (`moodle-plugin/block_moodlebot/`), embedded directly on course view pages with auto-context course detection.
2. **SQLite Persistence & Interaction Logging (`backend/db.py`)**: Implemented an ACID-compliant local relational database logging student questions, answers, sources, response latency, and ratings.
3. **Multi-Turn Conversation Memory**: Integrated dynamic session history in `backend/rag_chain.py` with intelligent followup retrieval query borrowing (e.g., *"give an example"* automatically recalls previous topic context).
4. **Student Privacy Protection (NFR-6)**: Enforced salted SHA-256 student hashing (32 hex characters) so student usernames and IDs are never stored in plaintext or exported.
5. **Security & Quality Control**: Integrated API Key authentication (`X-API-Key`), per-student sliding window rate limiting, and an automated test suite with **23 passing unit and integration tests (100% pass rate)**.
6. **Log Export Bridge (`backend/export_logs.py`)**: Built an automated exporter transforming live student chat logs into gradable evaluation CSV files compatible with `score.py`.

---

## 2. System Architecture & Week 5 Component Flow

```mermaid
sequenceDiagram
    autonumber
    actor Student
    participant Moodle as Moodle Course Page
    participant Block as MoodleBot Block (chat.js / ajax.php)
    participant FastAPI as FastAPI Backend (:8000)
    participant DB as SQLite (moodlebot.db)
    participant RAG as RAG Engine (rag_chain.py)
    participant Groq as Groq LPU (Qwen 2.5 27B)

    Student->>Moodle: Visits Course Page (e.g., DBMS)
    Moodle->>Block: Renders chat widget with courseid & sesskey
    Student->>Block: Enters question ("What is 3NF?")
    Block->>FastAPI: POST /chat (course_id, question, student_id, session_id)
    FastAPI->>FastAPI: Verifies X-API-Key & Rate Limit; Hashes student_id
    FastAPI->>DB: get_history(session_id, student_hash)
    FastAPI->>RAG: answer(question, history, subject)
    RAG->>RAG: _retrieval_query() reformulates followup
    RAG->>Groq: Generate grounded answer with capped history
    Groq-->>RAG: Synthesized answer + citations
    RAG-->>FastAPI: answer + sources
    FastAPI->>DB: log_interaction(question, answer, sources, latency)
    FastAPI-->>Block: JSON { answer, sources, session_id, interaction_id }
    Block-->>Student: Renders Markdown response + citation badges + 👍/👎 buttons
    Student->>Block: Clicks "👍 Helpful"
    Block->>FastAPI: POST /feedback (interaction_id, rating=1)
    FastAPI->>DB: set_feedback(interaction_id, rating=1)
```

---

## 3. Key Implementations

### 3.1 Moodle Block Plugin (`moodle-plugin/block_moodlebot/`)
- **Plugin Identifier:** `block_moodlebot` (v0.2.0, build `2026101100`).
- **AJAX Proxy Architecture (`ajax.php`)**: The student's browser never directly connects to the Python backend or sees the `MOODLEBOT_API_KEY`. Instead, `ajax.php` validates the active Moodle login, `sesskey`, and course capability, then securely proxies the request to the FastAPI backend.
- **XSS-Safe DOM Rendering (`chat.js`)**: All incoming LLM text is parsed and injected via safe DOM nodes (`document.createElement`), completely preventing script injection or malicious prompt payload execution.
- **Contextual Course Detection**: Automatically pulls `$course->id` and passes it to the backend so answers are contextualized without requiring manual student configuration.
- **Docker Mount**: Added `./moodle-plugin/block_moodlebot:/bitnami/moodle/blocks/moodlebot` to `docker-compose.yml` for zero-configuration container startup.

### 3.2 Backend Persistence & Multi-Turn Sessions (`backend/db.py`)
- Schema `interactions` holds:
  - `id`: Auto-incrementing primary key
  - `session_id`: Client session UUID
  - `student_hash`: Salted SHA-256 hash (32 hex characters)
  - `course_id`: Subject/course identifier
  - `question` & `answer`: Query and synthesized response
  - `sources`: JSON array of retrieved slide paths
  - `response_time_s`: Real-time query latency in seconds
  - `rating`: Rating integer (`+1` helpful, `-1` unhelpful, `NULL` unrated)
  - `created_at`: ISO-8601 UTC timestamp
- **Session Transcript Endpoint**: `GET /history/{session_id}?student_id=...` allows students to reload their active conversation while preventing other students from reading their transcripts.
- **Feedback Endpoint**: `POST /feedback` accepts `{ student_id, interaction_id, rating }` with strict validation (`rating in (1, -1)`).

### 3.3 Multi-Turn RAG Query Expansion (`backend/rag_chain.py`)
- **`_retrieval_query(question, history)`**: When students ask short followups (e.g., *"give an example"* or *"why?"*), the engine automatically borrows the previous user question to preserve vector search relevance.
- **`generate(question, chunks, history)`**: Formats conversation turns into OpenAI chat structure with capped history (`MAX_HISTORY_TURNS = 3`), ensuring context is only passed on the active turn.
- **`warmup()`**: Pre-loads embeddings into memory during application lifespan to eliminate cold-start latency on first user query.

### 3.4 Student Privacy & Security
- **Salted SHA-256 Student Hashing**: Real student IDs (e.g. `moodle-user-4711`) are hashed using a university server secret salt (`MOODLEBOT_SALT`).
- **API Key Guard**: Endpoints are protected via `MOODLEBOT_API_KEY` header verification (`X-API-Key`).
- **Sliding-Window Rate Limiting**: Enforces `RATE_LIMIT_PER_MIN` to prevent denial-of-service or token exhaustion attacks.

---

## 4. Automated Testing & Verification Suite

A comprehensive test suite of **23 automated tests** was executed via `pytest`, achieving a **100% pass rate**:

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-8.3.3
rootdir: C:\Users\pafro\OneDrive\Desktop\MoodleBot\backend
collected 23 items

tests/test_api.py::test_health PASSED                                    [  4%]
tests/test_api.py::test_chat_creates_session_and_logs PASSED             [  8%]
tests/test_api.py::test_followup_receives_history PASSED                 [ 13%]
tests/test_api.py::test_sessions_are_isolated_between_students PASSED    [ 17%]
tests/test_api.py::test_student_id_is_not_stored_in_plaintext PASSED     [ 21%]
tests/test_api.py::test_api_key_required_when_configured PASSED          [ 26%]
tests/test_api.py::test_rate_limit PASSED                                [ 30%]
tests/test_api.py::test_input_validation PASSED                          [ 34%]
tests/test_api.py::test_feedback_flow PASSED                             [ 39%]
tests/test_api.py::test_pipeline_setup_error_maps_to_503 PASSED          [ 43%]
tests/test_api.py::test_pipeline_unexpected_error_maps_to_502 PASSED     [ 47%]
tests/test_logs_and_startup.py::test_export_rows_are_gradable_and_anonymous PASSED [ 52%]
tests/test_logs_and_startup.py::test_export_csv_is_compatible_with_score_py PASSED [ 56%]
tests/test_logs_and_startup.py::test_smoke_test_traffic_is_excluded_from_exports PASSED [ 60%]
tests/test_logs_and_startup.py::test_filters_by_course_and_date PASSED   [ 65%]
tests/test_logs_and_startup.py::test_summary_statistics PASSED           [ 69%]
tests/test_logs_and_startup.py::test_sample_is_reproducible_and_does_not_exceed_log PASSED [ 73%]
tests/test_logs_and_startup.py::test_failing_warmup_does_not_prevent_the_api_from_serving PASSED [ 78%]
tests/test_rag_history.py::test_short_followup_borrows_previous_question_for_retrieval PASSED [ 82%]
tests/test_rag_history.py::test_long_question_is_not_modified PASSED     [ 86%]
tests/test_rag_history.py::test_no_history_leaves_question_alone PASSED  [ 91%]
tests/test_rag_history.py::test_generate_sends_history_then_context_only_on_last_turn PASSED [ 95%]
tests/test_rag_history.py::test_history_is_capped PASSED                 [100%]

============================= 23 passed in 9.80s ==============================
```

---

## 5. Summary of Week 5 Deliverables

| Deliverable | Path | Status |
|---|---|---|
| **Moodle Block Plugin** | `moodle-plugin/block_moodlebot/` | Complete (PHP/JS, secure AJAX proxy, XSS-safe chat UI) |
| **SQLite Persistence Layer** | `backend/db.py` | Complete (ACID interactions table, sessions, ratings) |
| **Backend API Engine** | `backend/main.py` | Complete (`/chat`, `/history`, `/feedback`, auth, rate limit) |
| **RAG Multi-Turn Memory** | `backend/rag_chain.py` | Complete (`MAX_HISTORY_TURNS=3`, query expansion, warmup) |
| **Live Chat Export Utility** | `backend/export_logs.py` | Complete (Exports anonymous evaluation CSVs for `score.py`) |
| **Integration Test Suite** | `backend/tests/` | Complete (**23/23 tests passing**) |
| **Interactive UI Rating** | `backend/static/index.html` | Complete (Session continuity, thumbs up/down widget) |
| **Docker Volume Mounting** | `docker-compose.yml` | Complete (Mounts block plugin directly into Moodle container) |

---

## 6. Transition to Week 6: Student Pilot & TAM Study

With the LMS plugin embedded, persistence verified, and 23 automated tests passing:
1. **Deploy Pilot with Student Cohort**: Launch MoodleBot across 50+ students in active DBMS and Programming courses.
2. **Execute Technology Acceptance Model (TAM) Survey**: Distribute standardized 5-point Likert scale questionnaires measuring:
   - **Perceived Usefulness (PU)**
   - **Perceived Ease of Use (PEOU)**
   - **Attitude Toward Using (ATU)**
   - **Behavioral Intention (BI)**
3. **Analyze Live Telemetry & Feedback**: Run `python export_logs.py --stats` to track student satisfaction rates, latency distributions, and common questions.
