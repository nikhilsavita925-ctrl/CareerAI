"""
A simple, explainable ATS (Applicant Tracking System) score.

Real ATS products use proprietary logic, but most agree on the same basics:
does the resume contain standard sections, is it a reasonable length, and how
many relevant/marketable skills does it surface. We score those 0-100 and
return concrete suggestions so the user knows what to fix.
"""

SECTION_KEYWORDS = {
    "contact": ["email", "phone", "@"],
    "education": ["education", "b.tech", "bachelor", "college", "university", "degree"],
    "experience": ["experience", "internship", "worked", "project"],
    "skills": ["skills", "technologies", "tools"],
    "projects": ["project"],
}


def calculate_ats_score(text: str, extracted_skills: list[str]) -> dict:
    text_lower = text.lower()
    word_count = len(text.split())

    section_hits = {}
    for section, keywords in SECTION_KEYWORDS.items():
        section_hits[section] = any(k in text_lower for k in keywords)

    section_score = (sum(section_hits.values()) / len(SECTION_KEYWORDS)) * 40  # up to 40 pts

    # Skill richness: up to 40 points, capped at 12 detected skills
    skill_score = min(len(extracted_skills), 12) / 12 * 40

    # Length: resumes that are too short or absurdly long lose points (up to 20 pts)
    if 250 <= word_count <= 900:
        length_score = 20
    elif word_count < 250:
        length_score = max(0, 20 - (250 - word_count) / 10)
    else:
        length_score = max(0, 20 - (word_count - 900) / 50)

    total = round(section_score + skill_score + length_score)
    total = max(0, min(100, total))

    suggestions = []
    for section, present in section_hits.items():
        if not present:
            suggestions.append(f"Add a clear '{section.title()}' section.")
    if len(extracted_skills) < 5:
        suggestions.append("List more relevant technical skills explicitly (e.g. in a Skills section).")
    if word_count < 250:
        suggestions.append("Your resume looks short — add more detail on projects/experience.")
    if word_count > 900:
        suggestions.append("Your resume is quite long — trim it to the most relevant 1-2 pages.")
    if not suggestions:
        suggestions.append("Looks solid! Tailor your skills section to each internship you apply for.")

    return {
        "score": total,
        "word_count": word_count,
        "sections_found": [s for s, present in section_hits.items() if present],
        "sections_missing": [s for s, present in section_hits.items() if not present],
        "suggestions": suggestions,
    }
