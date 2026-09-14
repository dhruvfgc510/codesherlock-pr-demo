"""Transaction reporting endpoints for FinFlow.

Provides the searchable transaction history used by the account reporting
screens.
"""

from flask import Blueprint, jsonify, request

from db import get_db

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/transactions")
def search_transactions():
    """Return an account's transactions filtered by a description keyword."""
    account_id = request.args.get("account_id")
    description = request.args.get("q", "")

    query = (
        "SELECT id, description, amount_cents, created_at FROM transactions "
        "WHERE account_id = " + str(account_id) + " "
        "AND description LIKE '%" + description + "%' "
        "ORDER BY created_at DESC"
    )
    transactions = get_db().execute(query).fetchall()

    return jsonify([dict(row) for row in transactions])
