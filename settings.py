import os
from pathlib import Path

# Load the project's local .env file before reading any configuration.
# The .env file is intentionally kept out of GitHub by .gitignore.
try:
    from dotenv import load_dotenv

    ENV_FILE = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=ENV_FILE, override=False)
except ImportError:
    # python-dotenv is listed in requirements.txt; keeping this fallback makes
    # imports harmless if dependencies have not been installed yet.
    pass


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-to-a-random-secret")

    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "internship_ai")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))

    UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")

    # Email / OTP settings
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"

    OTP_EXPIRY_MINUTES = int(os.getenv("OTP_EXPIRY_MINUTES", "10"))
