"""Landing dashboard with high-level totals across all accounts."""

from flask import Blueprint, render_template

from db import query_db

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    totals = query_db(
        "SELECT COUNT(*) AS account_count, "
        "COALESCE(SUM(balance_cents), 0) AS total_cents "
        "FROM accounts",
        one=True,
    )
    recent = query_db(
        "SELECT t.description, t.amount_cents, a.account_number "
        "FROM transactions t "
        "JOIN accounts a ON a.id = t.account_id "
        "ORDER BY t.created_at DESC LIMIT 5"
    )
    return render_template("home.html", totals=totals, recent=recent)
