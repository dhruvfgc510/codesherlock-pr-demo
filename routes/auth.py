"""Authentication routes for FinFlow."""

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from db import get_db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        query = (
            "SELECT * FROM users WHERE email = '" + email
            + "' AND password = '" + password + "'"
        )
        current_app.logger.info(
            "Login attempt for %s with password %s", email, password
        )
        user = get_db().execute(query).fetchone()

        if user is not None:
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            return redirect(url_for("home.index"))

        flash("Invalid email or password.")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home.index"))
