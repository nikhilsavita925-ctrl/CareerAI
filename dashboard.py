import os
import uuid
import re

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
)

from auth import login_required
from db import query

from utils.resume_parser import (
    extract_text,
    extract_skills,
    allowed_file,
)

from utils.ats_score import calculate_ats_score
from utils.recommender import recommend_internships


# ============================================================
# BLUEPRINT
# ============================================================

dashboard_bp = Blueprint("dashboard", __name__)


# ============================================================
# COMPANY REQUIREMENTS
# ============================================================
# These are the entry-level requirements used by our
# Company Resume Match feature.
#
# The resume is compared against these skills.
# ============================================================

COMPANY_REQUIREMENTS = {

    "Google": {

        "role": "University Graduate / Entry-Level Software Roles",

        "skills": [
            "python",
            "java",
            "c++",
            "go",
            "sql",
            "data structures",
            "algorithms",
            "problem solving",
        ],

        "focus": (
            "Programming, DSA, SQL, problem solving "
            "and communication."
        ),

        "education": (
            "Bachelor's, Master's or equivalent practical "
            "experience in Computer Science, Engineering, "
            "Mathematics or related fields."
        ),

    },


    "TCS": {

        "role": "Ninja / Digital / Prime",

        "skills": [
            "python",
            "java",
            "c++",
            "oop",
            "sql",
            "dbms",
            "data structures",
            "algorithms",
        ],

        "focus": (
            "OOP, DSA, DBMS, programming "
            "and analytical reasoning."
        ),

        "education": (
            "B.E., B.Tech, M.E., M.Tech, MCA "
            "or M.Sc depending on the role."
        ),

    },


    "Infosys": {

        "role": "Systems Engineer / Specialist Programmer",

        "skills": [
            "python",
            "java",
            "c++",
            "oop",
            "sql",
            "dbms",
            "rest api",
            "problem solving",
            "software development",
        ],

        "focus": (
            "Programming, OOP, DBMS, SDLC, "
            "REST APIs and problem solving."
        ),

        "education": (
            "Relevant graduation degree with strong "
            "programming and problem-solving fundamentals."
        ),

    },

}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_company_list():
    """
    Converts COMPANY_REQUIREMENTS dictionary into a list
    which can easily be displayed inside Jinja templates.
    """

    companies = []

    for company_name, data in COMPANY_REQUIREMENTS.items():

        companies.append({
            "name": company_name,
            "role": data["role"],
            "skills": data["skills"],
            "focus": data["focus"],
            "education": data["education"],
        })

    return companies


def skill_exists(skill, resume_skills, resume_text):
    """
    Checks whether a required skill exists in the resume.

    We check:
    1. extracted_skills from resume parser
    2. complete phrase in extracted resume text

    Regex word boundaries are used so that:
    'sql' doesn't accidentally match 'nosql'.
    """

    skill = skill.lower().strip()

    # -----------------------------------------
    # Check extracted skills
    # -----------------------------------------

    normalized_skills = [
        s.lower().strip()
        for s in resume_skills
        if s
    ]

    if skill in normalized_skills:
        return True

    # -----------------------------------------
    # Check complete phrase in resume text
    # -----------------------------------------

    if not resume_text:
        return False

    pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"

    return re.search(
        pattern,
        resume_text.lower()
    ) is not None


# ============================================================
# DASHBOARD
# ============================================================

@dashboard_bp.route("/dashboard")
@login_required
def dashboard():

    user_id = session["user_id"]

    # -----------------------------------------
    # Get logged-in user
    # -----------------------------------------

    user = query(
        """
        SELECT *
        FROM users
        WHERE id=%s
        """,
        (user_id,),
        fetchone=True
    )

    # -----------------------------------------
    # Get latest resume
    # -----------------------------------------

    latest_resume = query(
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

    # -----------------------------------------
    # Company data for dashboard
    # -----------------------------------------

    companies = get_company_list()

    return render_template(
        "dashboard.html",
        user=user,
        resume=latest_resume,
        companies=companies
    )


# ============================================================
# RESUME UPLOAD + ATS ANALYSIS
# ============================================================

@dashboard_bp.route(
    "/resume/upload",
    methods=["GET", "POST"]
)
@login_required
def upload_resume():

    # ========================================================
    # GET REQUEST
    # ========================================================

    if request.method == "GET":

        return render_template(
            "upload_resume.html"
        )


    # ========================================================
    # GET FILE
    # ========================================================

    file = request.files.get("resume")

    if not file or file.filename == "":

        flash(
            "Please select a resume file.",
            "danger"
        )

        return redirect(
            url_for("dashboard.upload_resume")
        )


    # ========================================================
    # CHECK FILE TYPE
    # ========================================================

    if not allowed_file(
        file.filename,
        {"pdf", "docx"}
    ):

        flash(
            "Only PDF and DOCX resumes are supported.",
            "danger"
        )

        return redirect(
            url_for("dashboard.upload_resume")
        )


    # ========================================================
    # CREATE UNIQUE FILE NAME
    # ========================================================

    original_filename = file.filename

    extension = (
        original_filename
        .rsplit(".", 1)[1]
        .lower()
    )

    unique_filename = (
        f"{uuid.uuid4().hex}.{extension}"
    )


    # ========================================================
    # UPLOAD FOLDER
    # ========================================================

    upload_folder = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "uploads"
    )

    os.makedirs(
        upload_folder,
        exist_ok=True
    )

    filepath = os.path.join(
        upload_folder,
        unique_filename
    )


    # ========================================================
    # SAVE RESUME
    # ========================================================

    try:

        file.save(filepath)

    except Exception as e:

        flash(
            f"Could not save resume: {str(e)}",
            "danger"
        )

        return redirect(
            url_for("dashboard.upload_resume")
        )


    # ========================================================
    # EXTRACT RESUME TEXT
    # ========================================================

    try:

        resume_text = extract_text(
            filepath
        )

    except Exception as e:

        if os.path.exists(filepath):
            os.remove(filepath)

        flash(
            f"Could not read the resume: {str(e)}",
            "danger"
        )

        return redirect(
            url_for("dashboard.upload_resume")
        )


    # ========================================================
    # EMPTY RESUME CHECK
    # ========================================================

    if not resume_text or not resume_text.strip():

        if os.path.exists(filepath):
            os.remove(filepath)

        flash(
            "No readable text was found in the resume.",
            "danger"
        )

        return redirect(
            url_for("dashboard.upload_resume")
        )


    # ========================================================
    # EXTRACT SKILLS
    # ========================================================

    try:

        skills = extract_skills(
            resume_text
        )

    except Exception as e:

        if os.path.exists(filepath):
            os.remove(filepath)

        flash(
            f"Could not analyze resume skills: {str(e)}",
            "danger"
        )

        return redirect(
            url_for("dashboard.upload_resume")
        )


    # ========================================================
    # ATS SCORE
    # ========================================================

    try:

        ats_result = calculate_ats_score(
            resume_text,
            skills
        )

    except Exception as e:

        if os.path.exists(filepath):
            os.remove(filepath)

        flash(
            f"Could not calculate ATS score: {str(e)}",
            "danger"
        )

        return redirect(
            url_for("dashboard.upload_resume")
        )


    # ========================================================
    # SAVE ANALYSIS TO DATABASE
    # ========================================================

    query(
        """
        INSERT INTO resumes
        (
            user_id,
            filename,
            extracted_text,
            extracted_skills,
            ats_score
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            session["user_id"],
            original_filename,
            resume_text,
            ", ".join(skills),
            ats_result["score"],
        ),
        commit=True
    )


    # ========================================================
    # SHOW RESULT
    # ========================================================

    return render_template(
        "resume_result.html",
        filename=original_filename,
        skills=skills,
        ats=ats_result
    )


# ============================================================
# COMPANY-SPECIFIC RESUME ANALYSIS
# ============================================================
#
# NEW FLOW:
#
# Dashboard
#      ↓
# Select ONE company
#      ↓
# Company-specific resume upload page
#      ↓
# Upload resume
#      ↓
# Extract text + skills
#      ↓
# Compare against selected company's requirements
#      ↓
# Company-specific match result
#
# The normal /resume/upload flow remains untouched.
# ============================================================


def _company_result_data(company_name, resume_text, resume_skills):
    """Build one company-specific resume match result."""

    company_data = COMPANY_REQUIREMENTS[company_name]
    required_skills = company_data["skills"]

    normalized_skills = [
        skill.strip().lower()
        for skill in resume_skills
        if skill and skill.strip()
    ]

    normalized_text = (resume_text or "").lower()

    matched_skills = []
    missing_skills = []

    for skill in required_skills:
        if skill_exists(
            skill,
            normalized_skills,
            normalized_text
        ):
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    total_required = len(required_skills)

    if total_required:
        match_percentage = round(
            (len(matched_skills) / total_required) * 100
        )
    else:
        match_percentage = 0

    if match_percentage >= 80:
        recommendation = (
            "Strong match. Your resume is closely aligned "
            "with the listed requirements."
        )
    elif match_percentage >= 60:
        recommendation = (
            "Good match. Adding the missing skills could "
            "improve your alignment."
        )
    elif match_percentage >= 40:
        recommendation = (
            "Moderate match. Consider strengthening your "
            "technical skill coverage."
        )
    else:
        recommendation = (
            "Low match right now. Focus on the missing skills "
            "and relevant projects."
        )

    return {
        "company": company_name,
        "role": company_data["role"],
        "required_skills": required_skills,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "match_percentage": match_percentage,
        "focus": company_data["focus"],
        "education": company_data["education"],
        "recommendation": recommendation,
    }


# ============================================================
# COMPANY SELECTION ENTRY POINT
# ============================================================

@dashboard_bp.route(
    "/company-compare",
    methods=["GET", "POST"]
)
@login_required
def company_compare():
    """
    Compatibility entry point for the existing dashboard form.

    The old flow showed another company-selection page here.
    That page is no longer used.

    The new flow accepts exactly one selected company and sends
    the user directly to that company's resume upload page.
    """

    if request.method == "GET":
        return redirect(
            url_for("dashboard.dashboard")
        )

    selected_companies = list(dict.fromkeys(
        company
        for company in request.form.getlist("companies")
        if company in COMPANY_REQUIREMENTS
    ))

    if not selected_companies:
        flash(
            "Please select a company first.",
            "warning"
        )
        return redirect(
            url_for("dashboard.dashboard")
        )

    if len(selected_companies) > 1:
        flash(
            "Please select only one company for company-specific resume analysis.",
            "warning"
        )
        return redirect(
            url_for("dashboard.dashboard")
        )

    return redirect(
        url_for(
            "dashboard.company_resume_upload",
            company_name=selected_companies[0]
        )
    )


# ============================================================
# COMPANY-SPECIFIC RESUME UPLOAD
# ============================================================

@dashboard_bp.route(
    "/company-resume/<company_name>",
    methods=["GET", "POST"]
)
@login_required
def company_resume_upload(company_name):
    """Upload a resume and analyze it specifically for one company."""

    if company_name not in COMPANY_REQUIREMENTS:
        flash(
            "Invalid company selected.",
            "danger"
        )
        return redirect(
            url_for("dashboard.dashboard")
        )

    company_data = COMPANY_REQUIREMENTS[company_name]

    # --------------------------------------------------------
    # GET: show selected company's upload page
    # --------------------------------------------------------

    if request.method == "GET":
        return render_template(
            "company_resume_upload.html",
            company_name=company_name,
            company=company_data
        )

    # --------------------------------------------------------
    # GET FILE
    # --------------------------------------------------------

    file = request.files.get("resume")

    if not file or file.filename == "":
        flash(
            "Please select a resume file.",
            "danger"
        )
        return redirect(
            url_for(
                "dashboard.company_resume_upload",
                company_name=company_name
            )
        )

    # --------------------------------------------------------
    # CHECK FILE TYPE
    # --------------------------------------------------------

    if not allowed_file(
        file.filename,
        {"pdf", "docx"}
    ):
        flash(
            "Only PDF and DOCX resumes are supported.",
            "danger"
        )
        return redirect(
            url_for(
                "dashboard.company_resume_upload",
                company_name=company_name
            )
        )

    # --------------------------------------------------------
    # CREATE UNIQUE FILE NAME
    # --------------------------------------------------------

    original_filename = file.filename
    extension = (
        original_filename
        .rsplit(".", 1)[1]
        .lower()
    )

    unique_filename = (
        f"{uuid.uuid4().hex}.{extension}"
    )

    # --------------------------------------------------------
    # UPLOAD FOLDER
    # --------------------------------------------------------

    upload_folder = os.path.join(
        os.path.dirname(
            os.path.abspath(__file__)
        ),
        "uploads"
    )

    os.makedirs(
        upload_folder,
        exist_ok=True
    )

    filepath = os.path.join(
        upload_folder,
        unique_filename
    )

    # --------------------------------------------------------
    # SAVE RESUME
    # --------------------------------------------------------

    try:
        file.save(filepath)
    except Exception as e:
        flash(
            f"Could not save resume: {str(e)}",
            "danger"
        )
        return redirect(
            url_for(
                "dashboard.company_resume_upload",
                company_name=company_name
            )
        )

    # --------------------------------------------------------
    # EXTRACT TEXT
    # --------------------------------------------------------

    try:
        resume_text = extract_text(filepath)
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)

        flash(
            f"Could not read the resume: {str(e)}",
            "danger"
        )
        return redirect(
            url_for(
                "dashboard.company_resume_upload",
                company_name=company_name
            )
        )

    if not resume_text or not resume_text.strip():
        if os.path.exists(filepath):
            os.remove(filepath)

        flash(
            "No readable text was found in the resume.",
            "danger"
        )
        return redirect(
            url_for(
                "dashboard.company_resume_upload",
                company_name=company_name
            )
        )

    # --------------------------------------------------------
    # EXTRACT SKILLS
    # --------------------------------------------------------

    try:
        skills = extract_skills(resume_text)
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)

        flash(
            f"Could not analyze resume skills: {str(e)}",
            "danger"
        )
        return redirect(
            url_for(
                "dashboard.company_resume_upload",
                company_name=company_name
            )
        )

    # --------------------------------------------------------
    # ATS SCORE
    # --------------------------------------------------------
    # Keep the existing ATS calculation for the uploaded resume.
    # The company-specific match is calculated separately below.
    # --------------------------------------------------------

    try:
        ats_result = calculate_ats_score(
            resume_text,
            skills
        )
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)

        flash(
            f"Could not calculate resume score: {str(e)}",
            "danger"
        )
        return redirect(
            url_for(
                "dashboard.company_resume_upload",
                company_name=company_name
            )
        )

    # --------------------------------------------------------
    # SAVE RESUME FOR CURRENT LOGGED-IN USER
    # --------------------------------------------------------

    query(
        """
        INSERT INTO resumes
        (
            user_id,
            filename,
            extracted_text,
            extracted_skills,
            ats_score
        )
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            session["user_id"],
            original_filename,
            resume_text,
            ", ".join(skills),
            ats_result["score"],
        ),
        commit=True
    )

    # --------------------------------------------------------
    # COMPANY-SPECIFIC MATCH
    # --------------------------------------------------------

    resume_skills = [
        skill.strip().lower()
        for skill in skills
        if skill and skill.strip()
    ]

    comparison_result = _company_result_data(
        company_name,
        resume_text,
        resume_skills
    )

    # --------------------------------------------------------
    # COMPANY RESULT PAGE
    # --------------------------------------------------------

    return render_template(
        "company_result.html",
        company_name=company_name,
        company=company_data,
        filename=original_filename,
        resume_skills=resume_skills,
        comparison_result=comparison_result,
        ats=ats_result
    )


# ============================================================
# INTERNSHIP RECOMMENDATIONS
# ============================================================

@dashboard_bp.route(
    "/recommendations"
)
@login_required
def recommendations():

    user_id = session["user_id"]


    # ========================================================
    # GET USER
    # ========================================================

    user = query(
        """
        SELECT *
        FROM users
        WHERE id=%s
        """,
        (user_id,),
        fetchone=True
    )


    # ========================================================
    # GET LATEST RESUME
    # ========================================================

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


    # ========================================================
    # GET STUDENT SKILLS
    # ========================================================

    student_skills = []


    if resume and resume.get(
        "extracted_skills"
    ):

        student_skills = [
            skill.strip()
            for skill in resume[
                "extracted_skills"
            ].split(",")
            if skill.strip()
        ]


    elif user and user.get("skills"):

        student_skills = [
            skill.strip()
            for skill in user[
                "skills"
            ].split(",")
            if skill.strip()
        ]


    # ========================================================
    # GET INTERNSHIPS
    # ========================================================

    internships = query(
        """
        SELECT *
        FROM internships
        ORDER BY id DESC
        """,
        fetchall=True
    )


    # ========================================================
    # GENERATE RECOMMENDATIONS
    # ========================================================

    results = recommend_internships(
        student_skills,
        internships,
        top_n=10
    )


    # ========================================================
    # RESULT PAGE
    # ========================================================

    return render_template(
        "recommendations.html",
        recommendations=results,
        student_skills=student_skills
    )