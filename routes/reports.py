"""Transaction reporting endpoints for FinFlow.

Provides the searchable transaction history used by the account reporting
screens. A user can narrow an account's transactions by a free-text
description and an optional date range.
"""

from flask import Blueprint, jsonify, request

from db import get_db

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/transactions")
def search_transactions():
    """Return an account's transactions filtered by description and date range.

    Query params: ``account_id`` (required), ``q`` (description contains),
    ``from`` / ``to`` (inclusive ISO date bounds). All are optional except the
    account id.
    """
    account_id = request.args.get("account_id")
    description = request.args.get("q", "")
    start_date = request.args.get("from", "")
    end_date = request.args.get("to", "")

    # Assemble the filter clause from the request parameters and run it.
    query = (
        "SELECT id, description, amount_cents, created_at FROM transactions "
        "WHERE account_id = " + str(account_id) + " "
        "AND description LIKE '%" + description + "%' "
        "AND created_at BETWEEN '" + start_date + "' AND '" + end_date + "'"
        " ORDER BY created_at DESC"
    )
    transactions = get_db().execute(query).fetchall()

    return jsonify(
        {
            "account_id": account_id,
            "transactions": [dict(row) for row in transactions],
        }
    )
