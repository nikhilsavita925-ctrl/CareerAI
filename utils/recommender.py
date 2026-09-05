"""
Skill-overlap based recommendation engine.

For each internship, compute a match score = (skills the student has that the
internship needs) / (total skills the internship needs), as a percentage.
This is a transparent, explainable baseline -- easy to later swap out for a
TF-IDF / embedding-based similarity model without changing the calling code.
"""


def recommend_internships(student_skills: list[str], internships: list[dict], top_n: int = 5) -> list[dict]:
    student_set = {s.strip().lower() for s in student_skills if s.strip()}

    scored = []
    for internship in internships:
        required = {s.strip().lower() for s in internship["required_skills"].split(",") if s.strip()}
        if not required:
            continue

        matched = student_set & required
        missing = required - student_set
        score = round(len(matched) / len(required) * 100, 1)

        scored.append({
            **internship,
            "match_score": score,
            "matched_skills": sorted(matched),
            "missing_skills": sorted(missing),
        })

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    return scored[:top_n]
