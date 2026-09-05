from flask import Blueprint, render_template, request, redirect, url_for, flash, session

from auth import login_required
from db import query


company_match_bp = Blueprint("company_match", __name__)


def calculate_company_match(resume_skills, required_skills):
    """
    Compare resume skills with company requirements.
    Returns match percentage, matched skills and missing skills.
    """

    student_skills = {
        skill.strip().lower()
        for skill in resume_skills
        if skill.strip()
    }

    required = {
        skill.strip().lower()
        for skill in required_skills
        if skill.strip()
    }

    if not required:
        return {
            "score": 0,
            "matched": [],
            "missing": []
        }

    matched = student_skills.intersection(required)
    missing = required - student_skills

    score = round((len(matched) / len(required)) * 100)

    return {
        "score": score,
        "matched": sorted(matched),
        "missing": sorted(missing)
    }


@company_match_bp.route("/company-match", methods=["GET", "POST"])
@login_required
def company_match():

    user_id = session["user_id"]

    # Latest analyzed resume
    resume = query(
        """
        SELECT *
        FROM resumes
        WHERE user_id=%s
        ORDER BY id DESC
        LIMIT 1
        """,
        (user_id,),
        fetchone=True
    )

    # All companies
    companies = query(
        """
        SELECT *
        FROM company_profiles
        ORDER BY company_name
        """,
    )

    selected_company = None
    result = None

    if request.method == "POST":

        company_id = request.form.get("company_id")

        selected_company = query(
            """
            SELECT *
            FROM company_profiles
            WHERE id=%s
            """,
            (company_id,),
            fetchone=True
        )

        if not resume:
            flash(
                "Please analyze your resume first.",
                "warning"
            )

            return redirect(
                url_for("dashboard.upload_resume")
            )

        if selected_company:

            resume_skills = []

            if resume.get("detected_skills"):
                resume_skills = [
                    skill.strip()
                    for skill in resume["detected_skills"].split(",")
                    if skill.strip()
                ]

            required_skills = selected_company[
                "required_skills"
            ].split(",")

            result = calculate_company_match(
                resume_skills,
                required_skills
            )

    return render_template(
        "company_match.html",
        companies=companies,
        selected_company=selected_company,
        result=result,
        resume=resume
    )