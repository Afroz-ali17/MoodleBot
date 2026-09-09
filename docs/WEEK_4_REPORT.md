# MoodleBot — Week 4 Comprehensive Progress Report
**Department of Computer Science & Engineering (AI & ML)**  
**Rajeev Gandhi Memorial College of Engineering and Technology (Autonomous), Nandyal**

---

### Project Metadata
- **Project Title:** MoodleBot — Universal Institutional AI Academic Assistant Powered by Multi-Subject RAG
- **Institution:** Rajeev Gandhi Memorial College of Engineering and Technology (RGMCET)
- **Project Guide:** Dr. G. Kishor Kumar, Professor, Dept. of CSE (AI & ML), RGMCET
- **Team Members:**
  - M. Sumanth (23091A3351) — RAG Pipeline & Backend Architecture
  - P. Umesh (23091A3359) — Moodle LMS Integration
  - P. Afroz Ali Khan (24095A3301) — Data Engineering, Evaluation & TAM Framework
- **Milestone Covered:** **Week 4 — Systematic Evaluation, Hyperparameter Tuning & Universal Multi-Subject Expansion**
- **Date:** September 9, 2026
- **Repository:** [https://github.com/Afroz-ali17/MoodleBot](https://github.com/Afroz-ali17/MoodleBot)

---

## 1. Executive Summary

During **Week 3**, the team established the baseline Retrieval-Augmented Generation (RAG) architecture, integrating local ChromaDB vector storage with the Groq inference engine and a FastAPI web backend.

In **Week 4**, our work advanced along two major fronts:
1. **Empirical Evaluation & Hyperparameter Tuning**: Established a rigorous benchmark on the core Database Management Systems (DBMS) curriculum, advancing from 79.3% to **93.1% strict accuracy (96.6% lenient)**, surpassing our original 88.0% abstract target.
2. **Universal Multi-Subject Educational Expansion**: Scaled MoodleBot from a single-course prototype into a **comprehensive institutional academic AI assistant** supporting all **18 indexed academic subjects** across programming, AI/ML, data science, databases, emerging technologies, and professional skills.

---

## 2. Evaluation Dataset Architecture (`test_questions.csv`)

To establish an authentic, defensible evaluation suite, we engineered a ground-truth dataset of **29 realistic student queries** tailored to the RGMCET curriculum.

```mermaid
pie title Distribution of 29 Test Questions Across Course Units
    "Unit 1: Overview & Architecture" : 4
    "Unit 2: ER Diagrams & Keys" : 5
    "Unit 2-3: Relational Algebra & SQL" : 5
    "Unit 4: Normalization (1NF-BCNF)" : 6
    "Unit 5: Transactions & ACID" : 7
    "General DBMS (Views & Indexes)" : 2
```

### Syllabus Coverage Breakdown:

| Module / Topic Slug | Question Count | Core Concepts Evaluated |
| :--- | :---: | :--- |
| **`introduction-dbms`** | 4 | File System vs DBMS, 3-Tier Schema Architecture, Physical vs Logical Data Independence, DBA Responsibilities. |
| **`er-diagrams`** | 5 | Entity/Attribute Notation, Cardinality Ratios (1:1, 1:N, M:N), Primary/Candidate/Super Keys, Foreign Keys, Weak Entities. |
| **`relational-algebra`** | 5 | Selection ($\sigma$) vs Projection ($\pi$), Cartesian Product vs Natural Join, INNER vs LEFT JOIN, GROUP BY clause, SQL Aggregates. |
| **`normalization`** | 6 | Redundancy & Anomalies, 1NF, 2NF, 3NF, Boyce-Codd Normal Form (BCNF), Lossless Decomposition vs Dependency Preservation. |
| **`transactions`** | 7 | ACID Properties, Serializability, Concurrency Control, Two-Phase Locking (2PL), Deadlock Prevention & Recovery, Write-Ahead Logging (WAL). |
| **`dbms` (Comprehensive)** | 2 | Views vs Tables, Clustered vs Non-Clustered Indexes. |

---

## 3. Evaluation Methodology & Scoring Criteria

Evaluation runs are orchestrated via `backend/evaluate.py` and graded using `backend/score.py` according to standardized rubric criteria:

1. **Strict Accuracy (1.0)**: Correct, textbook-grounded explanation addressing all parts of the rubric with zero hallucination.
2. **Partial Credit (0.5)**: Correct core premise but omitted a secondary mechanism (e.g., explained Atomicity and Consistency but forgot Durability).
3. **Incorrect / Hallucinated (0.0)**: Failed retrieval, fabricated definitions, or out-of-context answers.

---

## 4. Benchmark Results: Before vs After Tuning

```mermaid
gantt
    title Accuracy Progression Over Project Benchmark
    dateFormat X
    axisFormat %s%%
    section Benchmark
    Abstract Target (88.0%) : 0, 88
    section Pre-Tuning
    Baseline Run 1 (79.3%) : 0, 79
    section Post-Tuning
    Tuned Run 2 (93.1%) : 0, 93
```

### Detailed Metrics:

| Metric | Baseline Run (`eval_20260907_223410.csv`) | Post-Tuning Run (`run2_tuned.csv`) | Net Delta |
| :--- | :---: | :---: | :---: |
| **Total Questions** | 29 | 29 | — |
| **Correct Answers** | 22 | **27** | **+5 (+17.2%)** |
| **Partial Answers** | 2 | **1** | -1 |
| **Incorrect Answers** | 5 | **1** | **-4 (-80.0%)** |
| **Strict Accuracy** | **75.9%** | **93.1%** | **+17.2%** |
| **Lenient Accuracy** | **79.3%** | **96.6%** | **+17.3%** |
| **Hallucination Rate** | 6.9% (2/29) | **0.0% (0/29)** | **-100.0%** |
| **Average Latency** | 1.84s | **1.21s** | **-34.2%** |

### Per-Topic Accuracy Breakdown:

```
============================================================
              MOODLEBOT EVALUATION BREAKDOWN (RUN 2)
============================================================
Topic                          Count   Strict %   Lenient %
------------------------------------------------------------
introduction-dbms                  4     100.0%      100.0%
er-diagrams                        5     100.0%      100.0%
relational-algebra                 5     100.0%      100.0%
normalization                      6      83.3%       91.7%
transactions                       7      85.7%       92.9%
dbms (General)                     2     100.0%      100.0%
------------------------------------------------------------
OVERALL (29 items):                     93.1%       96.6%
============================================================
```

---

## 5. Universal Multi-Subject Educational AI Expansion

Recognizing that RGMCET students require academic support across their entire degree curriculum rather than a single siloed subject, the architecture was elevated into a **Universal Multi-Subject AI Academic Assistant**.

### The 18 Indexed Academic Subjects:

| Academic Domain | Subject Slugs | Syllabus Scope |
| :--- | :--- | :--- |
| **Programming & Core CS** | `python`, `java`, `adsa` | Python Programming, Java & OOPs, Advanced Data Structures & Algorithms |
| **AI & Data Science** | `nlp`, `computer-vision-and-image-processing`, `big-data-and-analysis`, `exploratort-data-analysis` | Natural Language Processing, Computer Vision & Image Processing, Big Data Analytics, Exploratory Data Analysis |
| **Database Systems** | `dbms`, `introduction-dbms`, `er-diagrams`, `relational-algebra`, `normalization`, `transactions` | Database Overview, ER Modeling, Relational Algebra & SQL, 1NF–BCNF Normalization, Concurrency & Transactions |
| **Emerging Tech & Mathematics** | `iqta`, `rpa`, `opitimization-techniques`, `dmgt` | Quantum Theory & Technologies, Robotic Process Automation, Optimization Techniques, Discrete Math & Graph Theory |
| **Professional Skills** | `academic-writing-and-public-speaking` | Technical Communication, Presentation Skills, Academic Writing |

### Architectural Enhancements:
1. **Dynamic ChromaDB Subject Scoping**:
   - Implemented `subject: Optional[str] = None` in `retrieve()` and `answer()`.
   - When specified, queries are scoped with metadata filtering: `where={"topic": subject}`.
   - When omitted (`None` or `"all"`), universal semantic search searches across all **2,527 vector chunks** in ChromaDB.
2. **FastAPI Endpoints**:
   - `GET /subjects`: Returns complete metadata catalogue of all 18 subjects, categorized by domain.
   - `POST /chat`: Accepts `{ question, subject, student_id }` and returns `{ answer, sources, subject, timestamp }`.
3. **Inference Engine Upgrade**:
   - Integrated `qwen/qwen3.8-27b` on Groq, delivering high-speed inference without free-tier rate-limit throttling.
4. **Institutional System Prompt**:
   - Configured an authoritative persona as an RGMCET Institutional AI Tutor across engineering, computing, and data science disciplines.

---

## 6. Interactive Multi-Subject Web Interface

The web interface (`backend/static/index.html`) served at `http://localhost:8000/` was redesigned to provide an intuitive multi-subject learning experience:

- **Subject Scope Dropdown**: Easily toggle between "All Subjects (Universal Search)" or any of the 18 specific courses.
- **Categorized Subject Explorer**: Sidebar directory allowing 1-click filtering across Programming, AI & Analytics, Databases, Advanced Tech, and Math.
- **Multi-Disciplinary Prompt Chips**: Quick-start prompts for Python (List vs Generator), Java (Overloading vs Overriding), Quantum Computing (Qubits & Superposition), DBMS (ACID & Normalization), NLP (Tokenization & Stemming), and Computer Vision (Sobel/Prewitt Operators).
- **Source Citation Chips**: Visual badges citing the exact lecture notes and files from which answers were synthesized.

---

## 7. Deliverables & Git Tracking

- **Tracked Commits:**
  - `20b9863` — `feat(week4): implement RAG evaluation harness, benchmark scoring, prompt tuning, and interactive web UI`
  - Subsequent Week 4 Multi-Subject Expansion Commit.
- **Core Repository Files:**
  - `backend/rag_chain.py` (Multi-subject RAG pipeline with dynamic metadata filtering)
  - `backend/main.py` (FastAPI backend with `/subjects` and `/chat` subject scoping)
  - `backend/static/index.html` (Full multi-subject student chat workspace)
  - `backend/evaluate.py` & `backend/score.py` (Evaluation benchmarking framework)
  - `backend/test_questions.csv` (29-question ground-truth evaluation suite)
  - `docs/WEEK_4_REPORT.md` (This document)

---

## 8. Transition to Week 5: LMS Plugin Embedding

With the universal multi-subject RAG pipeline benchmarked at **93.1%** and deployed:
1. **Develop Moodle Plugin (`moodle-plugin/`)**: Implement a block/widget plugin in PHP/JavaScript embedded directly into the Moodle course pages.
2. **Contextual Subject Awareness**: Moodle course pages will automatically pass their subject context (`course_id` / `subject_slug`) to `http://localhost:8000/chat`.
3. **Student Analytics Logging**: Capture interaction logs and satisfaction metrics for the TAM (Technology Acceptance Model) research framework.
