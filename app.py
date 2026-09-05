import os

from flask import Flask, render_template

from settings import Config
import db

from auth import auth_bp
from dashboard import dashboard_bp
from company_match import company_match_bp


def create_app():

    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Create uploads folder if it doesn't exist
    os.makedirs(
        app.config["UPLOAD_FOLDER"],
        exist_ok=True
    )

    # Initialize database
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(company_match_bp)

    # Home page
    @app.route("/")
    def home():
        return render_template("index.html")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )