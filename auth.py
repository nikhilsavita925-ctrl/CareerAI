from datetime import datetime, timedelta
from email.message import EmailMessage
import secrets
import smtplib

from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash

from db import query


auth_bp = Blueprint("auth", __name__)


def login_required(view):
    """Decorator: redirect to /login if no user is in the session."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


def ensure_pending_table():
    """Create the temporary registration table if it does not exist."""
    query(
        """
        CREATE TABLE IF NOT EXISTS pending_registrations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            fullname VARCHAR(120) NOT NULL,
            email VARCHAR(150) NOT NULL UNIQUE,
            phone VARCHAR(20),
            college VARCHAR(150),
            course VARCHAR(100),
            semester INT,
            skills TEXT,
            otp_hash VARCHAR(255) NOT NULL,
            otp_expires_at DATETIME NOT NULL,
            otp_verified TINYINT(1) NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        commit=True,
    )


def send_otp_email(recipient_email, otp):
    """Send a registration OTP through the configured SMTP sender account."""
    username = current_app.config.get("MAIL_USERNAME", "").strip()
    password = current_app.config.get("MAIL_PASSWORD", "").strip()
    server = current_app.config.get("MAIL_SERVER", "smtp.gmail.com")
    port = int(current_app.config.get("MAIL_PORT", 587))
    use_tls = current_app.config.get("MAIL_USE_TLS", True)

    if not username or not password:
        raise RuntimeError(
            "Email is not configured. Set MAIL_USERNAME and MAIL_PASSWORD in your .env file."
        )

    msg = EmailMessage()
    msg["Subject"] = "CareerAI - Verify your email"
    msg["From"] = username
    msg["To"] = recipient_email
    msg.set_content(
        f"""Hi,

Your CareerAI verification OTP is: {otp}

This OTP is valid for {current_app.config.get('OTP_EXPIRY_MINUTES', 10)} minutes.
Do not share this code with anyone.

If you did not try to create a CareerAI account, you can ignore this email.

Regards,
CareerAI Team
"""
    )

    with smtplib.SMTP(server, port, timeout=20) as smtp:
        smtp.ehlo()
        if use_tls:
            smtp.starttls()
            smtp.ehlo()
        smtp.login(username, password)
        smtp.send_message(msg)


def send_welcome_email(recipient_email, fullname):
    """Send a confirmation after the account is actually created."""
    username = current_app.config.get("MAIL_USERNAME", "").strip()
    password = current_app.config.get("MAIL_PASSWORD", "").strip()
    server = current_app.config.get("MAIL_SERVER", "smtp.gmail.com")
    port = int(current_app.config.get("MAIL_PORT", 587))
    use_tls = current_app.config.get("MAIL_USE_TLS", True)

    if not username or not password:
        return

    msg = EmailMessage()
    msg["Subject"] = "Welcome to CareerAI - Account created"
    msg["From"] = username
    msg["To"] = recipient_email
    msg.set_content(
        f"""Hi {fullname},

Your CareerAI account has been successfully created.

You can now log in and start exploring AI-powered internship recommendations.

Regards,
CareerAI Team
"""
    )

    try:
        with smtplib.SMTP(server, port, timeout=20) as smtp:
            smtp.ehlo()
            if use_tls:
                smtp.starttls()
                smtp.ehlo()
            smtp.login(username, password)
            smtp.send_message(msg)
    except Exception:
        # Account creation must not fail just because a welcome email failed.
        current_app.logger.exception("Welcome email could not be sent")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        college = request.form.get("college", "").strip()
        course = request.form.get("course", "").strip()
        semester = request.form.get("semester") or None
        skills = request.form.get("skills", "").strip()

        errors = []
        if not fullname or not email:
            errors.append("Full name and email are required.")
        if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            errors.append("Please enter a valid email address.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("register.html", form=request.form)

        ensure_pending_table()

        existing = query("SELECT id FROM users WHERE email=%s", (email,), fetchone=True)
        if existing:
            flash("An account with this email already exists. Please log in.", "danger")
            return render_template("register.html", form=request.form)

        # A fresh OTP replaces any previous pending registration for this email.
        otp = f"{secrets.randbelow(1000000):06d}"
        otp_hash = generate_password_hash(otp)
        expires_at = datetime.now() + timedelta(
            minutes=current_app.config.get("OTP_EXPIRY_MINUTES", 10)
        )

        query("DELETE FROM pending_registrations WHERE email=%s", (email,), commit=True)
        pending_id = query(
            """
            INSERT INTO pending_registrations
                (fullname, email, phone, college, course, semester, skills,
                 otp_hash, otp_expires_at, otp_verified)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
            """,
            (fullname, email, phone, college, course, semester, skills,
             otp_hash, expires_at),
            commit=True,
        )

        try:
            send_otp_email(email, otp)
        except Exception as exc:
            query("DELETE FROM pending_registrations WHERE id=%s", (pending_id,), commit=True)
            current_app.logger.exception("OTP email could not be sent")
            flash(f"OTP could not be sent. Check your email settings. ({exc})", "danger")
            return render_template("register.html", form=request.form)

        session["pending_registration_id"] = pending_id
        session["pending_registration_email"] = email
        flash("OTP sent to your email. Enter it to continue.", "success")
        return redirect(url_for("auth.verify_otp"))

    return render_template("register.html", form={})


@auth_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    pending_id = session.get("pending_registration_id")
    email = session.get("pending_registration_email")

    if not pending_id or not email:
        flash("Please start registration again.", "warning")
        return redirect(url_for("auth.register"))

    pending = query(
        "SELECT * FROM pending_registrations WHERE id=%s AND email=%s",
        (pending_id, email),
        fetchone=True,
    )

    if not pending:
        session.pop("pending_registration_id", None)
        session.pop("pending_registration_email", None)
        flash("Your registration session expired. Please start again.", "warning")
        return redirect(url_for("auth.register"))

    if request.method == "POST":
        otp = request.form.get("otp", "").strip()

        if datetime.now() > pending["otp_expires_at"]:
            flash("This OTP has expired. Please register again to receive a new OTP.", "danger")
            return render_template("verify_otp.html", email=email)

        if not check_password_hash(pending["otp_hash"], otp):
            flash("Incorrect OTP. Please try again.", "danger")
            return render_template("verify_otp.html", email=email)

        query(
            "UPDATE pending_registrations SET otp_verified=1 WHERE id=%s",
            (pending_id,),
            commit=True,
        )
        session["otp_verified"] = True
        return redirect(url_for("auth.set_password"))

    return render_template("verify_otp.html", email=email)


@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    pending_id = session.get("pending_registration_id")
    email = session.get("pending_registration_email")

    if not pending_id or not email:
        flash("Please start registration again.", "warning")
        return redirect(url_for("auth.register"))

    pending = query(
        "SELECT * FROM pending_registrations WHERE id=%s AND email=%s",
        (pending_id, email),
        fetchone=True,
    )
    if not pending:
        session.clear()
        flash("Your registration session expired. Please start again.", "warning")
        return redirect(url_for("auth.register"))

    otp = f"{secrets.randbelow(1000000):06d}"
    otp_hash = generate_password_hash(otp)
    expires_at = datetime.now() + timedelta(
        minutes=current_app.config.get("OTP_EXPIRY_MINUTES", 10)
    )
    query(
        "UPDATE pending_registrations SET otp_hash=%s, otp_expires_at=%s, otp_verified=0 WHERE id=%s",
        (otp_hash, expires_at, pending_id),
        commit=True,
    )

    try:
        send_otp_email(email, otp)
    except Exception as exc:
        current_app.logger.exception("OTP resend email could not be sent")
        flash(f"OTP could not be sent. Check your email settings. ({exc})", "danger")
        return redirect(url_for("auth.verify_otp"))

    session["otp_verified"] = False
    flash("A new OTP has been sent to your email.", "success")
    return redirect(url_for("auth.verify_otp"))


@auth_bp.route("/set-password", methods=["GET", "POST"])
def set_password():
    pending_id = session.get("pending_registration_id")
    email = session.get("pending_registration_email")

    if not pending_id or not email or not session.get("otp_verified"):
        flash("Please verify your email with OTP first.", "warning")
        return redirect(url_for("auth.register"))

    pending = query(
        "SELECT * FROM pending_registrations WHERE id=%s AND email=%s AND otp_verified=1",
        (pending_id, email),
        fetchone=True,
    )
    if not pending:
        session.clear()
        flash("Your registration session is no longer valid. Please start again.", "warning")
        return redirect(url_for("auth.register"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("set_password.html")
        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("set_password.html")

        existing = query("SELECT id FROM users WHERE email=%s", (email,), fetchone=True)
        if existing:
            query("DELETE FROM pending_registrations WHERE id=%s", (pending_id,), commit=True)
            session.clear()
            flash("An account with this email already exists. Please log in.", "danger")
            return redirect(url_for("auth.login"))

        password_hash = generate_password_hash(password)
        query(
            """INSERT INTO users
               (fullname, email, phone, college, course, semester, skills, password_hash)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (pending["fullname"], pending["email"], pending["phone"], pending["college"],
             pending["course"], pending["semester"], pending["skills"], password_hash),
            commit=True,
        )

        query("DELETE FROM pending_registrations WHERE id=%s", (pending_id,), commit=True)
        session.clear()
        send_welcome_email(email, pending["fullname"])
        flash("Account created successfully! You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("set_password.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = query("SELECT * FROM users WHERE email=%s", (email,), fetchone=True)

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["fullname"] = user["fullname"]
            flash(f"Welcome back, {user['fullname']}!", "success")
            return redirect(url_for("dashboard.dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))
