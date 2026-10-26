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
from werkzeug.security import check_password_hash

from db import get_db

auth_bp = Blueprint("auth", __name__)


def _mask_email(email):
    """Mask the local part of an email to reduce PII exposure in logs."""
    try:
        local, domain = email.split("@", 1)
        if len(local) <= 2:
            masked_local = local[0] + "*" * (len(local) - 1)
        else:
            masked_local = local[0] + "*" * (len(local) - 2) + local[-1]
        return f"{masked_local}@{domain}"
    except (ValueError, IndexError):
        return "unknown"


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        masked = _mask_email(email)
        ip = request.remote_addr or "unknown"

        # Audit log — never record the password or any other secret.
        current_app.logger.info("Login attempt for %s from %s", masked, ip)

        # Parameterized query prevents SQL injection: user input is bound as
        # data, never concatenated into the SQL text.
        user = get_db().execute(
            "SELECT id, role, password FROM users WHERE email = ?",
            (email,),
        ).fetchone()

        # Constant-time hash comparison; passwords are stored as salted hashes.
        if user is not None and check_password_hash(user["password"], password):
            # Rotate the session on privilege change to prevent fixation.
            session.clear()
            session["user_id"] = user["id"]
            session["role"] = user["role"]
            current_app.logger.info(
                "Login success for %s user_id=%s from %s", masked, user["id"], ip
            )
            return redirect(url_for("home.index"))

        current_app.logger.warning("Login failure for %s from %s", masked, ip)
        flash("Invalid email or password.")

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home.index"))
