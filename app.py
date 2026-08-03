"""FinFlow — a small fintech dashboard used to demo CodeSherlock PR reviews."""

import os

from flask import Flask

import db
from routes.home import home_bp
from routes.accounts import accounts_bp
from routes.auth import auth_bp
from routes.payments import payments_bp
from routes.search import search_bp


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
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

    @app.cli.command("init-db")
    def init_db_command():
        """Create tables and load seed data (run once before first start)."""
        with app.app_context():
            db.init_db()
        print("Initialized the FinFlow database.")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
