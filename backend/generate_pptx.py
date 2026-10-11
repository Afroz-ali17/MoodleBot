"""
Generate MoodleBot Project Review 1 Presentation (.pptx)
Covers all 12 required sections for the 1st Project Review.
"""
from pptx import slide
import sys, pathlib
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ── Colour palette ──
BG       = RGBColor(0x0F, 0x17, 0x2A)
CARD_BG  = RGBColor(0x1A, 0x20, 0x40)
PRIMARY  = RGBColor(0x63, 0x66, 0xF1)
ACCENT   = RGBColor(0x8B, 0x5C, 0xF6)
CYAN     = RGBColor(0x06, 0xB6, 0xD4)
GREEN    = RGBColor(0x10, 0xB9, 0x81)
AMBER    = RGBColor(0xF5, 0x9E, 0x0B)
ROSE     = RGBColor(0xF4, 0x3F, 0x5E)
WHITE    = RGBColor(0xF1, 0xF5, 0xF9)
MUTED    = RGBColor(0x94, 0xA3, 0xB8)
DIM      = RGBColor(0x64, 0x74, 0x8B)
BORDER   = RGBColor(0x1E, 0x29, 0x3B)

prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)

BLANK = prs.slide_layouts[6]  # blank layout

def set_bg(slide, color=BG):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_text(slide, left, top, width, height, text, size=14, bold=False,
             color=WHITE, align=PP_ALIGN.LEFT, font_name="Calibri"):
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = font_name
    p.alignment = align
    return tf

def add_para(tf, text, size=14, bold=False, color=WHITE, space_before=6, bullet=False, font_name="Calibri"):
    p = tf.add_paragraph()
    p.text = text
    p.font.size = Pt(size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = font_name
    p.space_before = Pt(space_before)
    if bullet:
        p.level = 0
    return p

def add_rounded_rect(slide, left, top, width, height, fill_color=CARD_BG):
    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left), Inches(top), Inches(width), Inches(height)
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.color.rgb = BORDER
    shape.line.width = Pt(1)
    shape.shadow.inherit = False
    return shape

def slide_header(slide, number, title):
    """Add consistent slide number + title bar."""
    add_text(slide, 0.6, 0.3, 4, 0.3, f"SLIDE {number}", size=9, bold=True, color=PRIMARY)
    add_text(slide, 0.6, 0.55, 10, 0.6, title, size=28, bold=True, color=WHITE)
    # Thin accent line
    line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.15), Inches(12.1), Pt(2))
    line.fill.solid()
    line.fill.fore_color.rgb = PRIMARY
    line.line.fill.background()

# ════════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE & OVERVIEW
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK); set_bg(s)

# Badge
badge = add_rounded_rect(s, 3.5, 0.8, 6.3, 0.45, PRIMARY)
add_text(s, 3.5, 0.82, 6.3, 0.4, "🎓  1st Project Review — Department of CSE (AI & ML)",
         size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

# Title
add_text(s, 1, 1.6, 11.3, 1.0, "MoodleBot", size=48, bold=True, color=WHITE, align=PP_ALIGN.CENTER)

# Subtitle
add_text(s, 1.5, 2.6, 10.3, 0.8,
         "An Intelligent Multi-Subject Educational Chatbot Powered by\n"
         "Retrieval-Augmented Generation (RAG) Integrated into Moodle LMS",
         size=16, color=MUTED, align=PP_ALIGN.CENTER)

# Team members
members = [
    ("M. Sumanth", "23091A3351", "RAG Pipeline & Backend"),
    ("P. Umesh", "23091A3359", "Moodle LMS Integration"),
    ("P. Afroz Ali Khan", "24095A3301", "Data Eng. & Evaluation"),
]
for i, (name, roll, role) in enumerate(members):
    x = 2.8 + i * 2.8
    box = add_rounded_rect(s, x, 3.8, 2.4, 1.5, CARD_BG)
    add_text(s, x, 3.9, 2.4, 0.35, name, size=13, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(s, x, 4.25, 2.4, 0.3, roll, size=10, color=DIM, align=PP_ALIGN.CENTER)
    add_text(s, x, 4.55, 2.4, 0.5, role, size=10, color=MUTED, align=PP_ALIGN.CENTER)

# Guide
add_text(s, 1, 5.6, 11.3, 0.5,
         "Project Guide: Dr. G. Kishor Kumar, Professor, Dept. of CSE (AI & ML), RGMCET (Autonomous), Nandyal",
         size=12, color=MUTED, align=PP_ALIGN.CENTER)

# Institution
add_text(s, 1, 6.2, 11.3, 0.5,
         "Rajeev Gandhi Memorial College of Engineering and Technology (Autonomous), Nandyal",
         size=11, color=DIM, align=PP_ALIGN.CENTER)

# Tech tags
tags_text = "Natural Language Processing  •  Vector Embeddings  •  LLM Inference  •  Moodle LMS  •  FastAPI"
add_text(s, 1, 6.7, 11.3, 0.4, tags_text, size=10, color=CYAN, align=PP_ALIGN.CENTER)

# ════════════════════════════════════════════════════════════════
# SLIDE 2 — ABSTRACT
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK); set_bg(s)
slide_header(s, 2, "Abstract")

tf = add_text(s, 0.6, 1.4, 12.1, 3.5,
    "Modern engineering students face a persistent challenge: accessing precise, contextually relevant "
    "academic guidance outside classroom hours. Traditional chatbots rely on generic internet knowledge "
    "and frequently hallucinate inaccurate information, undermining trust in AI-assisted learning.",
    size=13, color=MUTED)

add_para(tf, "", size=6)
add_para(tf,
    "MoodleBot addresses this by implementing a Retrieval-Augmented Generation (RAG) architecture that "
    "grounds every response exclusively in the institution's own course materials — lecture slides, "
    "syllabus PDFs, and faculty notes — guaranteeing factually accurate, citation-backed explanations.",
    size=13, color=WHITE, space_before=10)

add_para(tf, "", size=6)
add_para(tf,
    "The system integrates a ChromaDB vector store (2,527 embedded knowledge chunks from 93 course files "
    "across 18 academic subjects), a Sentence-BERT embedding model (all-MiniLM-L6-v2) for semantic retrieval, "
    "and a cloud-hosted LLM (Qwen 2.5 27B via Groq) for grounded generation — all served through a FastAPI "
    "REST backend with an interactive web interface and a planned Moodle LMS plugin for in-platform embedding.",
    size=13, color=MUTED, space_before=10)

# Metrics boxes
metrics = [
    ("93.1%", "Strict Accuracy"),
    ("96.6%", "Lenient Accuracy"),
    ("0%", "Hallucination Rate"),
    ("18", "Academic Subjects"),
]
for i, (val, label) in enumerate(metrics):
    x = 0.8 + i * 3.1
    add_rounded_rect(s, x, 5.3, 2.7, 1.3, CARD_BG)
    add_text(s, x, 5.4, 2.7, 0.7, val, size=30, bold=True, color=PRIMARY, align=PP_ALIGN.CENTER)
    add_text(s, x, 6.1, 2.7, 0.4, label, size=10, bold=True, color=DIM, align=PP_ALIGN.CENTER)

# ════════════════════════════════════════════════════════════════
# SLIDE 3 — LITERATURE SURVEY
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK); set_bg(s)
slide_header(s, 3, "Literature Survey")

studies = [
    ("Lewis et al. (2020) — RAG",
     "Retrieval-Augmented Generation combining BERT retriever with BART generator",
     "Reduces hallucination by 40-60% vs vanilla generation",
     "Evaluated on open-domain QA; not adapted for institutional curricula"),
    ("Gao et al. (2024) — RAG Survey",
     "Comprehensive survey covering Naive, Advanced, and Modular RAG paradigms",
     "Chunking strategy and retrieval precision critical for domain accuracy",
     "Recommends but does not implement institutional-grade grounding"),
    ("Sentence-BERT (Reimers, 2019)",
     "Siamese BERT networks for semantically meaningful sentence embeddings",
     "Enables fast cosine-similarity search with strong semantic matching",
     "all-MiniLM-L6-v2 trades depth for speed; may miss highly technical content"),
    ("ChromaDB (2023)",
     "Open-source embedded vector store with metadata filtering",
     "Lightweight, zero-config, supports topic-based scoped queries",
     "Single-node; not designed for distributed multi-tenant deployments"),
    ("Moodle LMS Chatbot Plugins",
     "Existing plugins: block_chatbot, mod_dialogue (rule-based FAQ)",
     "Basic keyword search within course forums",
     "No semantic understanding; cannot synthesize multi-document explanations"),
]

headers = ["Study / System", "Approach", "Key Findings", "Limitations"]
col_widths = [2.6, 3.2, 3.2, 3.1]
y_start = 1.4
row_h = 0.95

# Header row
x = 0.6
for j, hdr in enumerate(headers):
    add_rounded_rect(s, x, y_start, col_widths[j], 0.4, PRIMARY)
    add_text(s, x + 0.1, y_start + 0.02, col_widths[j] - 0.2, 0.35, hdr, size=9, bold=True, color=WHITE)
    x += col_widths[j] + 0.05

for i, (study, approach, findings, limits) in enumerate(studies):
    y = y_start + 0.5 + i * row_h
    x = 0.6
    for j, txt in enumerate([study, approach, findings, limits]):
        c = WHITE if j == 0 else MUTED
        sz = 9 if j == 0 else 9
        b = j == 0
        add_text(s, x + 0.1, y, col_widths[j] - 0.2, row_h - 0.05, txt, size=sz, bold=b, color=c)
        x += col_widths[j] + 0.05

# ════════════════════════════════════════════════════════════════
# SLIDE 4 — RESEARCH GAPS
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK); set_bg(s)
slide_header(s, 4, "Research Gaps Identified")

gaps = [
    ("🚫", "Gap 1: No Curriculum-Grounded Educational RAG",
     "Existing RAG systems target open-domain QA using Wikipedia or web corpora. No published system implements RAG grounded exclusively in an institution's own lecture slides, syllabi, and faculty-authored course notes."),
    ("📚", "Gap 2: Single-Subject Limitation",
     "Prior educational chatbot prototypes are designed for a single course. Students pursuing multi-disciplinary degrees need cross-curricular support across 18+ subjects simultaneously."),
    ("🔗", "Gap 3: No LMS Integration",
     "General-purpose AI assistants operate outside the student's learning environment. No published work embeds a RAG-based academic assistant directly inside Moodle LMS course pages."),
    ("🎯", "Gap 4: Hallucination in Educational AI",
     "Generic LLMs hallucinate 15-30% of factual claims. In educational contexts, a single hallucinated definition causes cascading misunderstanding. No existing Moodle chatbot enforces strict context-only generation."),
]

for i, (icon, title, desc) in enumerate(gaps):
    col = i % 2
    row = i // 2
    x = 0.6 + col * 6.2
    y = 1.4 + row * 2.5
    add_rounded_rect(s, x, y, 5.9, 2.2, CARD_BG)
    add_text(s, x + 0.2, y + 0.15, 5.4, 0.4, f"{icon}  {title}", size=13, bold=True, color=WHITE)
    add_text(s, x + 0.2, y + 0.65, 5.4, 1.4, desc, size=11, color=MUTED)

# Footer contribution
tf = add_text(s, 0.6, 6.4, 12.1, 0.8,
    "Our Contribution: MoodleBot fills all four gaps — grounded in RGMCET's own 93 course files, "
    "supporting 18 subjects, integrated into Moodle LMS, and achieving 0% hallucination rate.",
    size=12, bold=True, color=GREEN)

# ════════════════════════════════════════════════════════════════
# SLIDE 5 — PROBLEM STATEMENT
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK); set_bg(s)
slide_header(s, 5, "Problem Statement")

# Main statement box
stmt_box = add_rounded_rect(s, 0.6, 1.4, 12.1, 1.6, CARD_BG)
# Red left accent
line = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.4), Pt(4), Inches(1.6)) if False else None
tf = add_text(s, 0.9, 1.5, 11.5, 1.4,
    "Engineering students at RGMCET lack access to an intelligent, always-available academic assistant "
    "that can provide accurate, curriculum-specific explanations grounded in their actual course materials. "
    "Existing solutions — generic AI chatbots, search engines, or peer forums — suffer from hallucinated "
    "content, lack of source traceability, absence of multi-subject support, and zero integration with "
    "the institutional Learning Management System (Moodle).",
    size=13, color=WHITE)

# Three challenge cards
challenges = [
    ("⏰", "Limited Faculty Availability",
     "Students can only interact with faculty during office hours. Doubts arising during self-study, evenings, weekends, and exam prep go unanswered for hours or days."),
    ("🤥", "AI Hallucination Risk",
     "Generic LLMs produce plausible but factually incorrect explanations that students cannot verify, leading to learning damage during exam preparation."),
    ("🔍", "No Source Traceability",
     "Students need to know which lecture note, slide, or unit a concept originates from — for trust and deeper study. Generic AI provides no citations."),
]

for i, (icon, title, desc) in enumerate(challenges):
    x = 0.6 + i * 4.1
    y = 3.4
    add_rounded_rect(s, x, y, 3.8, 2.8, CARD_BG)
    add_text(s, x + 0.2, y + 0.15, 3.4, 0.4, f"{icon}  {title}", size=12, bold=True, color=WHITE)
    add_text(s, x + 0.2, y + 0.65, 3.4, 2.0, desc, size=11, color=MUTED)

# ════════════════════════════════════════════════════════════════
# SLIDE 6 — OBJECTIVES
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK); set_bg(s)
slide_header(s, 6, "Project Objectives")

objectives = [
    (PRIMARY, "O1. Build Curriculum-Grounded RAG Pipeline",
     "Design and implement a RAG pipeline grounded in the institution's own course materials — targeting ≥ 88% accuracy on a ground-truth benchmark."),
    (CYAN, "O2. Universal Multi-Subject Support",
     "Support the complete RGMCET CSE (AI&ML) curriculum across 18+ subjects with dynamic subject-scoped retrieval."),
    (GREEN, "O3. Moodle LMS Integration",
     "Embed MoodleBot as a native plugin inside Moodle course pages with automatic course-context awareness."),
    (AMBER, "O4. Rigorous Empirical Evaluation",
     "Validate through automated batch testing, human-graded scoring, and iterative hyperparameter tuning with documented evidence."),
    (ROSE, "O5. Zero Hallucination Guarantee",
     "Enforce strict context-only generation through system prompt engineering. Target: 0% hallucination rate."),
    (ACCENT, "O6. Student Adoption Research (TAM)",
     "Assess student satisfaction using the Technology Acceptance Model — measuring perceived usefulness, ease of use, and intent."),
]

for i, (clr, title, desc) in enumerate(objectives):
    col = i % 2
    row = i // 2
    x = 0.6 + col * 6.2
    y = 1.4 + row * 1.85
    box = add_rounded_rect(s, x, y, 5.9, 1.6, CARD_BG)
    # Accent line
    accent = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Pt(4), Inches(1.6))
    accent.fill.solid(); accent.fill.fore_color.rgb = clr; accent.line.fill.background()
    add_text(s, x + 0.25, y + 0.12, 5.4, 0.35, title, size=12, bold=True, color=WHITE)
    add_text(s, x + 0.25, y + 0.55, 5.4, 0.95, desc, size=11, color=MUTED)

# ════════════════════════════════════════════════════════════════
# SLIDE 7 — PROPOSED MODULES
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK); set_bg(s)
slide_header(s, 7, "Proposed System Modules")

modules = [
    ("📄", "M1. Data Preprocessing", "prepare_data.py",
     "Extracts text from raw PDFs, PPTX, DOCX. Applies OCR fallback, Unicode cleanup, topic-slug auto-tagging."),
    ("🧬", "M2. Embedding & Ingestion", "ingest.py",
     "Chunks text (200w window, 40w overlap), embeds with MiniLM-L6-v2, stores 2,527 vectors in ChromaDB."),
    ("🔍", "M3. RAG Pipeline", "rag_chain.py",
     "Semantic retrieval (TOP_K=4) with subject metadata filtering → context assembly → grounded LLM generation."),
    ("⚡", "M4. API Backend", "main.py",
     "FastAPI server: POST /chat (Q&A), GET /subjects (18 subjects), GET /health, GET / (web UI)."),
    ("🖥️", "M5. Web Interface", "static/index.html",
     "Dark-mode chat UI with subject scope selector, sidebar browser, prompt chips, markdown rendering."),
    ("📊", "M6. Evaluation Suite", "evaluate.py, score.py",
     "Automated batch evaluation with rate-limiting, human grading, and side-by-side accuracy comparison."),
]

for i, (icon, title, fname, desc) in enumerate(modules):
    col = i % 3
    row = i // 3
    x = 0.6 + col * 4.1
    y = 1.4 + row * 2.85
    add_rounded_rect(s, x, y, 3.8, 2.5, CARD_BG)
    add_text(s, x + 0.2, y + 0.12, 3.4, 0.35, f"{icon}  {title}", size=12, bold=True, color=WHITE)
    add_text(s, x + 0.2, y + 0.5, 3.4, 0.3, fname, size=10, bold=True, color=CYAN)
    add_text(s, x + 0.2, y + 0.9, 3.4, 1.4, desc, size=11, color=MUTED)

# ════════════════════════════════════════════════════════════════
# SLIDE 8 — PIPELINE OVERVIEW
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK); set_bg(s)
slide_header(s, 8, "RAG Pipeline Overview")

# Offline pipeline
add_text(s, 0.6, 1.4, 5, 0.35, "OFFLINE INGESTION PIPELINE", size=11, bold=True, color=CYAN)

offline_steps = [
    ("📄", "Raw Course Files", "93 PDFs/PPTX/DOCX"),
    ("🔧", "prepare_data.py", "Text Extraction"),
    ("✂️", "ingest.py", "Chunk (200w/40w)"),
    ("🧬", "Sentence-BERT", "all-MiniLM-L6-v2"),
    ("🗄️", "ChromaDB", "2,527 vectors"),
]
for i, (icon, title, desc) in enumerate(offline_steps):
    x = 0.6 + i * 2.5
    add_rounded_rect(s, x, 1.85, 2.1, 1.1, CARD_BG)
    add_text(s, x, 1.9, 2.1, 0.35, f"{icon} {title}", size=10, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(s, x, 2.3, 2.1, 0.5, desc, size=9, color=DIM, align=PP_ALIGN.CENTER)
    if i < len(offline_steps) - 1:
        add_text(s, x + 2.1, 2.15, 0.4, 0.4, "→", size=16, bold=True, color=PRIMARY, align=PP_ALIGN.CENTER)

# Online pipeline
add_text(s, 0.6, 3.3, 5, 0.35, "ONLINE QUERY PIPELINE (REAL-TIME)", size=11, bold=True, color=GREEN)

online_steps = [
    ("💬", "Student Query", '"What is 3NF?"'),
    ("🧬", "Embed Query", "MiniLM-L6-v2"),
    ("🔍", "Semantic Search", "ChromaDB (TOP_K=4)"),
    ("📋", "Context Assembly", "Ranked Chunks"),
    ("🤖", "LLM Generation", "Qwen 2.5 27B"),
    ("✅", "Grounded Answer", "+ Source Citations"),
]
for i, (icon, title, desc) in enumerate(online_steps):
    x = 0.3 + i * 2.15
    add_rounded_rect(s, x, 3.75, 1.85, 1.1, CARD_BG)
    add_text(s, x, 3.8, 1.85, 0.35, f"{icon} {title}", size=9, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(s, x, 4.2, 1.85, 0.5, desc, size=8, color=DIM, align=PP_ALIGN.CENTER)
    if i < len(online_steps) - 1:
        add_text(s, x + 1.85, 4.05, 0.3, 0.3, "→", size=14, bold=True, color=GREEN, align=PP_ALIGN.CENTER)

# Key design decisions
add_text(s, 0.6, 5.2, 5, 0.3, "KEY DESIGN DECISIONS", size=11, bold=True, color=AMBER)
decisions = [
    "Chunking: 200-word sliding window with 40-word overlap — no definition split at boundaries",
    "Subject-Scoped Retrieval: Optional metadata filter prevents cross-course contamination",
    "System Prompt: Enforces strict 'context-only' generation with structured Markdown output",
    "Fallback Handling: Auto 413 truncation, rate-limit backoff, and model failover",
]
tf = add_text(s, 0.6, 5.5, 12.1, 1.8, "", size=11, color=MUTED)
for d in decisions:
    add_para(tf, f"▸  {d}", size=11, color=MUTED, space_before=4)

# ════════════════════════════════════════════════════════════════
# SLIDE 9 — SYSTEM ARCHITECTURE
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK); set_bg(s)
slide_header(s, 9, "System Architecture & Data Flow")

# Three-tier architecture
tiers = [
    (PRIMARY, "🖥️  Presentation Layer",
     "• Interactive Web Chat UI (index.html)\n• Moodle LMS Plugin Widget (planned)\n• Subject Scope Dropdown + Source Citations\n• REST API (Swagger at /docs)"),
    (GREEN, "⚙️  Application / Logic Layer",
     "• FastAPI Backend (main.py)\n• RAG Pipeline (rag_chain.py)\n• Data Preprocessing (prepare_data.py)\n• Ingestion Engine (ingest.py)"),
    (AMBER, "🗄️  Data / Storage Layer",
     "• ChromaDB Vector Store (2,527 chunks)\n• Processed Corpus (data/processed/)\n• Moodle LMS (Docker: MariaDB + Moodle 4.4)\n• Evaluation Results (backend/results/)"),
]

for i, (clr, title, desc) in enumerate(tiers):
    x = 0.6
    y = 1.4 + i * 1.85
    add_rounded_rect(s, x, y, 5.8, 1.6, CARD_BG)
    accent = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Pt(4), Inches(1.6))
    accent.fill.solid(); accent.fill.fore_color.rgb = clr; accent.line.fill.background()
    add_text(s, x + 0.25, y + 0.1, 5.2, 0.3, title, size=12, bold=True, color=WHITE)
    add_text(s, x + 0.25, y + 0.45, 5.2, 1.1, desc, size=10, color=MUTED)

# Right column — External services + Data flow
add_text(s, 6.8, 1.4, 5, 0.3, "EXTERNAL INTEGRATIONS", size=11, bold=True, color=CYAN)

add_rounded_rect(s, 6.8, 1.8, 5.8, 1.0, CARD_BG)
add_text(s, 7.0, 1.85, 5.4, 0.3, "☁️  Groq Cloud Inference", size=11, bold=True, color=WHITE)
add_text(s, 7.0, 2.2, 5.4, 0.5, "Qwen 2.5 27B — high-speed LLM inference (~1.2s avg)\nOpenAI-compatible API. No local GPU required.", size=10, color=MUTED)

add_rounded_rect(s, 6.8, 3.0, 5.8, 1.0, CARD_BG)
add_text(s, 7.0, 3.05, 5.4, 0.3, "🐋  Docker Compose Stack", size=11, bold=True, color=WHITE)
add_text(s, 7.0, 3.4, 5.4, 0.5, "Moodle 4.4 (Bitnami) on port 8080\nMariaDB 10.11 with health checks, persistent volumes", size=10, color=MUTED)

add_text(s, 6.8, 4.3, 5, 0.3, "DATA FLOW SUMMARY", size=11, bold=True, color=GREEN)
flow_steps = [
    "1. Student sends query via Web UI or Moodle plugin",
    "2. FastAPI receives request + optional subject scope",
    "3. Query embedded via Sentence-BERT (local)",
    "4. ChromaDB returns TOP_K=4 similar chunks",
    "5. Chunks assembled into context prompt",
    "6. Groq LLM generates grounded answer",
    "7. Response + source citations returned to student",
]
tf = add_text(s, 6.8, 4.65, 5.8, 2.5, "", size=10, color=MUTED)
for step in flow_steps:
    add_para(tf, step, size=10, color=MUTED, space_before=3)

# ════════════════════════════════════════════════════════════════
# SLIDE 10 — TECH STACK
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK); set_bg(s)
slide_header(s, 10, "Technology Stack & Tools")

tech_rows = [
    ("Language", "Python 3.11", "Core backend, data processing, RAG pipeline"),
    ("Web Framework", "FastAPI + Uvicorn", "REST API, auto Swagger docs, ASGI async"),
    ("Vector Database", "ChromaDB", "Persistent vector store with metadata filtering"),
    ("Embedding Model", "all-MiniLM-L6-v2", "384-dim Sentence-BERT, ~90MB, local inference"),
    ("LLM Inference", "Groq (Qwen 2.5 27B)", "Cloud-hosted LLM, ~1.2s latency, OpenAI-compat API"),
    ("LMS Platform", "Moodle 4.4 (Bitnami)", "Learning Management System, Docker containerized"),
    ("Containerization", "Docker Compose", "Moodle + MariaDB 10.11, health checks"),
    ("Data Processing", "PyMuPDF, python-pptx", "PDF/PPTX/DOCX text extraction with OCR fallback"),
    ("Frontend", "HTML/CSS/JS + marked.js", "Responsive dark-mode chat UI, Markdown rendering"),
    ("Version Control", "Git + GitHub", "github.com/Afroz-ali17/MoodleBot"),
]

# Table header
cols_x = [0.6, 3.2, 6.4]
cols_w = [2.5, 3.1, 6.1]
y = 1.4
for j, hdr in enumerate(["Layer", "Technology", "Purpose"]):
    add_rounded_rect(s, cols_x[j], y, cols_w[j], 0.4, PRIMARY)
    add_text(s, cols_x[j] + 0.1, y + 0.02, cols_w[j] - 0.2, 0.35, hdr, size=10, bold=True, color=WHITE)

for i, (layer, tech, purpose) in enumerate(tech_rows):
    ry = 1.9 + i * 0.5
    bg_c = CARD_BG if i % 2 == 0 else BG
    for j, txt in enumerate([layer, tech, purpose]):
        add_rounded_rect(s, cols_x[j], ry, cols_w[j], 0.45, bg_c)
        c = WHITE if j <= 1 else MUTED
        b = j == 0
        add_text(s, cols_x[j] + 0.1, ry + 0.05, cols_w[j] - 0.2, 0.35, txt, size=10, bold=b, color=c)

# ════════════════════════════════════════════════════════════════
# SLIDE 11 — IMPLEMENTATION & RESULTS
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK); set_bg(s)
slide_header(s, 11, "Partial Implementation & Experimental Results")

# Top metrics
top_metrics = [("2,527", "Vector Chunks"), ("93", "Course Files"), ("18", "Subjects"), ("29", "Test Queries")]
for i, (val, label) in enumerate(top_metrics):
    x = 0.6 + i * 3.1
    add_rounded_rect(s, x, 1.35, 2.7, 0.9, CARD_BG)
    add_text(s, x, 1.38, 2.7, 0.5, val, size=22, bold=True, color=PRIMARY, align=PP_ALIGN.CENTER)
    add_text(s, x, 1.85, 2.7, 0.3, label, size=9, bold=True, color=DIM, align=PP_ALIGN.CENTER)

# Accuracy bars
add_text(s, 0.6, 2.5, 6, 0.3, "ACCURACY PROGRESSION", size=11, bold=True, color=CYAN)

bars = [
    ("Abstract Target", "88.0%", 0.88, CARD_BG, GREEN),
    ("Baseline (Pre-Tune)", "89.7%", 0.897, CARD_BG, DIM),
    ("Final (Post-Tune)", "93.1%", 0.931, CARD_BG, PRIMARY),
]
for i, (label, pct_text, pct, bg, fill_clr) in enumerate(bars):
    y = 2.9 + i * 0.6
    add_text(s, 0.6, y, 2.2, 0.4, label, size=10, bold=True, color=MUTED, align=PP_ALIGN.RIGHT)
    # Track
    add_rounded_rect(s, 2.9, y + 0.05, 9.5, 0.35, CARD_BG)
    # Fill
    fill_w = 9.5 * pct
    fill = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(2.9), Inches(y + 0.05), Inches(fill_w), Inches(0.35))
    fill.fill.solid(); fill.fill.fore_color.rgb = fill_clr
    fill.line.fill.background()
    add_text(s, 2.9 + fill_w - 0.7, y + 0.06, 0.65, 0.3, pct_text, size=10, bold=True, color=WHITE, align=PP_ALIGN.RIGHT)

# Per-topic table
add_text(s, 0.6, 4.8, 6, 0.3, "PER-TOPIC ACCURACY (POST-TUNING)", size=11, bold=True, color=AMBER)

topics = [
    ("Introduction DBMS", "4", "100%"),
    ("ER Diagrams", "5", "100%"),
    ("Relational Algebra", "5", "100%"),
    ("Normalization", "6", "83.3%"),
    ("Transactions", "7", "85.7%"),
    ("General DBMS", "2", "100%"),
    ("OVERALL", "29", "93.1%"),
]

tx = [0.6, 3.5, 5.0]
tw = [2.8, 1.4, 1.8]
# Header
for j, h in enumerate(["Topic", "Count", "Accuracy"]):
    add_rounded_rect(s, tx[j], 5.15, tw[j], 0.3, PRIMARY)
    add_text(s, tx[j] + 0.1, 5.15, tw[j] - 0.2, 0.3, h, size=9, bold=True, color=WHITE)

for i, (topic, cnt, acc) in enumerate(topics):
    ry = 5.5 + i * 0.3
    b = i == len(topics) - 1
    acc_clr = GREEN if acc == "100%" else (AMBER if acc != "93.1%" else PRIMARY)
    if b: acc_clr = PRIMARY
    for j, (txt, clr) in enumerate([(topic, WHITE if b else MUTED), (cnt, MUTED), (acc, acc_clr)]):
        add_text(s, tx[j] + 0.1, ry, tw[j] - 0.2, 0.28, txt, size=9, bold=b, color=clr)

# Right side — tuning actions
add_text(s, 7.2, 4.8, 5, 0.3, "KEY TUNING ACTIONS", size=11, bold=True, color=CYAN)
actions = [
    "▸  Chunk size reduced: 250 → 200 words + 40w overlap",
    "▸  System prompt strengthened: structured Markdown, context-only",
    "▸  Subject-scoped retrieval: prevents cross-course contamination",
    "▸  LLM upgraded: groq/compound → Qwen 2.5 27B",
    "▸  Hallucination rate: eliminated (6.9% → 0%)",
    "▸  Average latency improved: 1.84s → 1.21s (-34%)",
]
tf = add_text(s, 7.2, 5.2, 5.4, 2.5, "", size=10, color=MUTED)
for a in actions:
    add_para(tf, a, size=10, color=MUTED, space_before=4)

# ════════════════════════════════════════════════════════════════
# SLIDE 12 — EVALUATION STRATEGY & ROADMAP
# ════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BLANK); set_bg(s)
slide_header(s, 12, "Evaluation Strategy & Project Roadmap")

# Left — Evaluation strategy
add_text(s, 0.6, 1.4, 5, 0.3, "EVALUATION FRAMEWORK", size=11, bold=True, color=CYAN)

eval_items = [
    ("📋", "Ground-Truth Benchmark",
     "29-question syllabus-aligned test suite with standardized rubric. Expanding to all 18 subjects."),
    ("⚙️", "Automated Pipeline",
     "evaluate.py runs all queries with rate-limiting. score.py computes strict/lenient accuracy."),
    ("📊", "TAM Survey (Planned)",
     "Technology Acceptance Model questionnaire for 50+ RGMCET students."),
    ("🔄", "Iterative Tuning",
     "Each tuning cycle produces dated CSV. compare_runs.py generates before/after reports."),
]

for i, (icon, title, desc) in enumerate(eval_items):
    y = 1.8 + i * 1.25
    add_rounded_rect(s, 0.6, y, 5.8, 1.05, CARD_BG)
    add_text(s, 0.8, y + 0.05, 5.3, 0.3, f"{icon}  {title}", size=11, bold=True, color=WHITE)
    add_text(s, 0.8, y + 0.4, 5.3, 0.6, desc, size=10, color=MUTED)

# Right — Roadmap
add_text(s, 6.8, 1.4, 5, 0.3, "10-WEEK PROJECT ROADMAP", size=11, bold=True, color=GREEN)

weeks = [
    ("W1", "Moodle Docker Setup", "done"),
    ("W2", "Data Preprocessing", "done"),
    ("W3", "RAG Pipeline & API", "done"),
    ("W4", "Evaluation & Tuning", "done"),
    ("W5", "Moodle Plugin", "current"),
    ("W6", "User Testing & TAM", "future"),
    ("W7", "Multi-Subject QA", "future"),
    ("W8", "Analytics & Dashboards", "future"),
    ("W9", "Final Report & Paper", "future"),
    ("W10", "Final Defense", "future"),
]

for i, (wk, label, status) in enumerate(weeks):
    col = i % 2
    row = i // 2
    x = 6.8 + col * 3.0
    y = 1.8 + row * 0.95
    clr = GREEN if status == "done" else (CYAN if status == "current" else DIM)
    dot_bg = PRIMARY if status == "done" else (GREEN if status == "current" else CARD_BG)
    
    # Dot
    dot = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y + 0.05), Inches(0.3), Inches(0.3))
    dot.fill.solid(); dot.fill.fore_color.rgb = dot_bg
    dot.line.color.rgb = clr; dot.line.width = Pt(1.5)
    add_text(s, x, y + 0.07, 0.3, 0.25, wk, size=8, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    
    # Label
    add_text(s, x + 0.35, y + 0.05, 2.5, 0.3, label, size=10, bold=(status != "future"), color=clr)

# Next steps
add_text(s, 6.8, 6.0, 5, 0.3, "IMMEDIATE NEXT STEPS (WEEKS 5-6)", size=10, bold=True, color=AMBER)
tf = add_text(s, 6.8, 6.3, 5.8, 1.0, "", size=9, color=MUTED)
add_para(tf, "▸  Develop Moodle block plugin (PHP + JS)", size=9, color=MUTED, space_before=2)
add_para(tf, "▸  Auto-pass course context to /chat endpoint", size=9, color=MUTED, space_before=2)
add_para(tf, "▸  Expand evaluation to NLP, Java, Python, Quantum", size=9, color=MUTED, space_before=2)
add_para(tf, "▸  Deploy TAM survey to 50+ students", size=9, color=MUTED, space_before=2)

# ════════════════════════════════════════════════════════════════
# SAVE
# ════════════════════════════════════════════════════════════════
out_path = pathlib.Path(__file__).parent.parent / "docs" / "MoodleBot_Project_Review_1.pptx"
prs.save(str(out_path))
print(f"Presentation saved to: {out_path}")
print(f"Total slides: {len(prs.slides)}")
