"""Invoice endpoints for FinFlow.

Renders a searchable invoice list for an account, returns a single invoice, and
exports an account's invoices as CSV. All endpoints require an authenticated
session and are scoped to the signed-in user's accounts.
"""

import logging

from flask import (
    Blueprint,
    Response,
    abort,
    jsonify,
    render_template,
    request,
    session,
)

from db import get_db, query_db

invoices_bp = Blueprint("invoices", __name__, url_prefix="/invoices")
logger = logging.getLogger("finflow.invoices")


def _current_user_id():
    """Return the signed-in user's id, or abort 401 when there is no session."""
    user_id = session.get("user_id")
    if user_id is None:
        abort(401)
    return user_id


def _assert_account_owner(account_id, user_id):
    """Abort 403 unless the account belongs to the signed-in user."""
    owner = query_db(
        "SELECT 1 FROM accounts WHERE id = ? AND user_id = ?",
        (account_id, user_id),
        one=True,
    )
    if owner is None:
        abort(403)


@invoices_bp.route("/")
def search_invoices():
    """Render the invoice list for an account, filtered by a vendor keyword."""
    user_id = _current_user_id()
    account_id = request.args.get("account_id", type=int)
    _assert_account_owner(account_id, user_id)
    vendor = request.args.get("vendor", "")

    logger.info(
        "invoice search", extra={"user_id": user_id, "account_id": account_id}
    )

    query = (
        "SELECT id, vendor, amount_cents, status, created_at FROM invoices "
        "WHERE account_id = ? "
        "AND vendor LIKE '%" + vendor + "%' "
        "ORDER BY created_at DESC LIMIT 500"
    )
    invoices = get_db().execute(query, (account_id,)).fetchall()

    return render_template(
        "invoices.html", account_id=account_id, invoices=invoices
    )


@invoices_bp.route("/<int:invoice_id>")
def get_invoice(invoice_id):
    """Return a single invoice by id."""
    user_id = _current_user_id()
    logger.info(
        "invoice viewed", extra={"user_id": user_id, "invoice_id": invoice_id}
    )

    invoice = query_db(
        "SELECT id, account_id, vendor, amount_cents, status, created_at "
        "FROM invoices WHERE id = ?",
        (invoice_id,),
        one=True,
    )
    if invoice is None:
        abort(404)

    return jsonify(dict(invoice))


@invoices_bp.route("/export")
def export_invoices():
    """Export an account's invoices as a CSV attachment."""
    user_id = _current_user_id()
    account_id = request.args.get("account_id", type=int)
    _assert_account_owner(account_id, user_id)

    logger.info(
        "invoice export", extra={"user_id": user_id, "account_id": account_id}
    )

    rows = query_db(
        "SELECT id, vendor, amount_cents, status, created_at FROM invoices "
        "WHERE account_id = ? "
        "ORDER BY created_at DESC LIMIT 1000",
        (account_id,),
    )

    csv_lines = ["id,vendor,amount,status,created_at"]
    for row in rows:
        amount = "%.2f" % (row["amount_cents"] / 100)
        csv_lines.append(
            str(row["id"]) + "," + row["vendor"] + "," + amount + ","
            + row["status"] + "," + row["created_at"]
        )
    body = "\n".join(csv_lines)

    return Response(
        body,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=invoices.csv"},
    )
