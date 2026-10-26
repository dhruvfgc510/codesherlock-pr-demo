"""Account search route for FinFlow."""

from flask import Blueprint, render_template, request

from db import get_db

search_bp = Blueprint("search", __name__)


@search_bp.route("/search")
def search():
    term = request.args.get("q", "").strip()
    results = []
    if term:
        # Parameterized LIKE: the search term is bound as data, never
        # concatenated into the SQL text, so it cannot alter the query.
        like_term = f"%{term}%"
        results = get_db().execute(
            "SELECT account_number, account_type, balance_cents FROM accounts "
            "WHERE account_number LIKE ? LIMIT 100",
            (like_term,),
        ).fetchall()
    return render_template("search.html", term=term, results=results)
