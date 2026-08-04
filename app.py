"""FinFlow — a small fintech dashboard used to demo CodeSherlock PR reviews."""

import logging
import os

from flask import Flask

import db
from routes.home import home_bp
from routes.accounts import accounts_bp
from routes.auth import auth_bp
from routes.payments import payments_bp
from routes.search import search_bp
from routes.support import support_bp


def create_app():
    app = Flask(__name__)

    # Configure structured application logging early (level via LOG_LEVEL) so
    # every subsequent event goes through the logger, not ad-hoc prints.
    log_level = getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    app.logger.setLevel(log_level)

    # Treat the app as production unless an explicit local-dev signal is set.
    # Secure-by-default: a missing/insecure config must fail closed, not open.
    is_dev = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "on")

    # Never ship a meaningful secret in source and never use a predictable
    # default. Require a real SECRET_KEY in production; allow only an ephemeral
    # random key for local development (regenerated each start, never committed).
    secret = os.environ.get("SECRET_KEY")
    if not secret:
        if is_dev:
            secret = os.urandom(32)
            app.logger.warning(
                "No SECRET_KEY set; using an ephemeral random key for local "
                "development only. Set SECRET_KEY for any real deployment."
            )
        else:
            raise RuntimeError(
                "SECRET_KEY is required. Set it via the environment or a "
                "secret manager (only local development may run without one)."
            )
    app.config["SECRET_KEY"] = secret

    # Enforce standard session-cookie protections. HttpOnly always; Secure is
    # required in production (HTTPS) and relaxed only for local HTTP dev.
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = not is_dev
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    app.config["DATABASE"] = os.environ.get(
        "DATABASE", os.path.join(app.instance_path, "finflow.sqlite")
    )

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    app.register_blueprint(home_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(support_bp)

    @app.cli.command("init-db")
    def init_db_command():
        """Create tables and load seed data (run once before first start)."""
        try:
            with app.app_context():
                db.init_db()
            app.logger.info("Initialized the FinFlow database.")
        except Exception:
            app.logger.exception("Failed to initialize the FinFlow database.")
            raise

    return app


if __name__ == "__main__":
    # `python app.py` is the local development entrypoint: mark it as dev so
    # create_app() allows an ephemeral key and relaxes the Secure-cookie flag.
    # Debug is enabled here for local convenience but can be turned off with
    # FLASK_DEBUG=0. Production never reaches this path — it runs under a WSGI
    # server via the module-level `app` below, where debug is never enabled.
    os.environ.setdefault("FLASK_DEBUG", "1")
    debug = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "on")
    app = create_app()
    if debug:
        app.logger.warning("Running in DEBUG mode (development only).")
    app.run(debug=debug)
else:
    # Imported by a WSGI server (e.g. `gunicorn app:app`): production defaults
    # apply, so a real SECRET_KEY must be provided or startup fails fast.
    app = create_app()
