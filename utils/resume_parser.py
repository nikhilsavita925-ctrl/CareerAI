"""
Resume parsing.

- extract_text(filepath): pulls raw text out of a PDF or DOCX resume.
- extract_skills(text): matches the resume text against KNOWN_SKILLS.

Requires: pypdf (PDF) and python-docx (DOCX) -- see requirements.txt.
"""

import os
import re
from .skills_data import KNOWN_SKILLS


def extract_text(filepath: str) -> str:
    ext = filepath.rsplit(".", 1)[-1].lower()

    if ext == "pdf":
        from pypdf import PdfReader
        reader = PdfReader(filepath)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        return text

    if ext == "docx":
        import docx
        doc = docx.Document(filepath)
        return "\n".join(p.text for p in doc.paragraphs)

    raise ValueError(f"Unsupported resume format: .{ext}")


def extract_skills(text: str) -> list[str]:
    """Case-insensitive whole-word/phrase match against the known skill list."""
    text_lower = text.lower()
    found = []
    for skill in KNOWN_SKILLS:
        # word-boundary match so "r" doesn't match inside "for", etc.
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, text_lower):
            found.append(skill)
    return found


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions
