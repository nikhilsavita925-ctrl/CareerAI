# CareerAI — AI Resume Analysis & Internship Matching

CareerAI is a Flask-based web application that analyzes resumes, calculates ATS-style scores, extracts skills, compares a resume with selected companies, and provides internship recommendations.

## Features

- User registration, login and OTP verification
- Resume upload and text/skill extraction
- ATS-style resume scoring
- Company-specific resume matching
- Match percentage with matched and missing skills
- Internship recommendations based on skill overlap
- Premium responsive web interface
- MySQL database integration

## Tech Stack

- **Backend:** Python, Flask
- **Frontend:** HTML, CSS, JavaScript
- **Database:** MySQL
- **Resume processing:** PDF / DOCX parsing
- **Recommendation:** Skill-overlap based matching

## Project Structure

```text
CareerAI/
├── app.py
├── auth.py
├── company_match.py
├── dashboard.py
├── db.py
├── settings.py
├── schema.sql
├── requirements.txt
├── .env.example
├── .gitignore
├── static/
├── templates/
├── utils/
└── uploads/
```

## Setup

### 1. Clone the repository

```bash
git clone <your-github-repository-url>
cd CareerAI
```

### 2. Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and add your local MySQL and email credentials.

**Never commit `.env` to GitHub.**

### 5. Create the database

Create the MySQL database and run the SQL in `schema.sql`.

### 6. Run the application

```bash
python app.py
```

Then open the local address shown in the terminal.

## Security Note

Uploaded resumes, Python cache files, local databases, and environment files are excluded from version control. Configure secrets through environment variables rather than committing passwords or API credentials.

## Disclaimer

The ATS score and company match are intended as an educational/project-level recommendation and should not be treated as an official hiring decision.

## Email OTP registration

Registration now works as: **profile + email -> OTP -> verify OTP -> create password -> account created -> welcome email**.

1. Copy `.env.example` to `.env`.
2. Put your MySQL password in `MYSQL_PASSWORD`.
3. Put a Gmail sender account in `MAIL_USERNAME` and its Google App Password in `MAIL_PASSWORD`.
4. Run `pip install -r requirements.txt`.
5. Run the SQL in `schema.sql` (or let the app create `pending_registrations` automatically after the DB connection works).
6. Start with `python app.py`.

The sender Gmail is only the account that sends mail. OTPs can be delivered to any user's email address.
