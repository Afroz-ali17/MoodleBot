"""
Week 2 data collection helper.

Drop raw course materials into data/raw/ using this naming convention:
    <topic-slug>__<original-filename>.pdf/.pptx/.docx

Example:
    er-diagrams__lecture3_slides.pptx
    normalization__week4_notes.pdf

Run:
    python prepare_data.py

Output:
    data/processed/<topic-slug>/<filename>.txt   (cleaned text)
    data/processed/manifest.csv                  (index of everything processed)
"""

import os
import re
import csv
import pathlib

import pdfplumber
from pptx import Presentation
from docx import Document

RAW_DIR = pathlib.Path(__file__).parent.parent / "data" / "raw"
PROCESSED_DIR = pathlib.Path(__file__).parent.parent / "data" / "processed"


def clean_text(text: str) -> str:
    """Basic cleanup: collapse whitespace, drop obvious page-number-only lines."""
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if re.fullmatch(r"\d{1,3}", stripped):  # bare page number
            continue
        if re.fullmatch(r"page\s*\d+", stripped, re.IGNORECASE):
            continue
        cleaned.append(stripped)
    text = "\n".join(cleaned)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pdf(path: pathlib.Path) -> str:
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    return "\n".join(text_parts)


def extract_pptx(path: pathlib.Path) -> str:
    prs = Presentation(path)
    text_parts = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    line = "".join(run.text for run in para.runs)
                    if line.strip():
                        text_parts.append(line)
    return "\n".join(text_parts)


def extract_docx(path: pathlib.Path) -> str:
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


EXTRACTORS = {
    ".pdf": extract_pdf,
    ".pptx": extract_pptx,
    ".docx": extract_docx,
}


def parse_topic_slug(filename: str) -> tuple[str, str]:
    """Split 'topic-slug__original-name.ext' into (topic_slug, original_name).
    Falls back to 'uncategorized' if the '__' convention wasn't followed."""
    stem = pathlib.Path(filename).stem
    if "__" in stem:
        topic, original = stem.split("__", 1)
        return topic, original
    return "uncategorized", stem


def main():
    if not RAW_DIR.exists() or not any(RAW_DIR.iterdir()):
        print(f"No files found in {RAW_DIR}. Add course materials there first.")
        print("Naming convention: <topic-slug>__<filename>.pdf (e.g. normalization__week4_notes.pdf)")
        return

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    manifest_rows = []

    for file_path in sorted(RAW_DIR.iterdir()):
        if file_path.suffix.lower() not in EXTRACTORS:
            print(f"Skipping unsupported file type: {file_path.name}")
            continue

        topic_slug, original_name = parse_topic_slug(file_path.name)
        extractor = EXTRACTORS[file_path.suffix.lower()]

        try:
            raw_text = extractor(file_path)
        except Exception as e:
            print(f"FAILED to extract {file_path.name}: {e}")
            continue

        cleaned = clean_text(raw_text)

        topic_dir = PROCESSED_DIR / topic_slug
        topic_dir.mkdir(parents=True, exist_ok=True)
        out_path = topic_dir / f"{original_name}.txt"
        out_path.write_text(cleaned, encoding="utf-8")

        word_count = len(cleaned.split())
        manifest_rows.append({
            "source_file": file_path.name,
            "topic": topic_slug,
            "output_path": str(out_path.relative_to(PROCESSED_DIR.parent.parent)),
            "word_count": word_count,
        })
        print(f"Processed: {file_path.name} -> {out_path.name} ({word_count} words, topic={topic_slug})")

    manifest_path = PROCESSED_DIR / "manifest.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["source_file", "topic", "output_path", "word_count"])
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(f"\nDone. {len(manifest_rows)} files processed.")
    print(f"Manifest written to {manifest_path}")


if __name__ == "__main__":
    main()
