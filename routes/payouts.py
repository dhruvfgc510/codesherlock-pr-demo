"""Payout endpoints for FinFlow.

Handles outbound payouts from a customer account to a saved payee: viewing a
single payout, approving a pending payout, and exporting a payout history as
CSV. All endpoints require an authenticated session.
"""

from flask import (
    Blueprint,
    Response,
    abort,
    jsonify,
    redirect,
    request,
    session,
    url_for,
)

from db import get_db, query_db

payouts_bp = Blueprint("payouts", __name__, url_prefix="/payouts")


def current_user_id():
    """Return the signed-in user's id, or abort with 401 if there is no session."""
    user_id = session.get("user_id")
    if user_id is None:
        abort(401)
    return user_id


@payouts_bp.route("/<int:payout_id>")
def view_payout(payout_id):
    """Show the details of a single payout."""
    current_user_id()

    payout = query_db(
        "SELECT id, account_id, payee_id, amount_cents, status, created_at "
        "FROM payouts WHERE id = ?",
        (payout_id,),
        one=True,
    )
    if payout is None:
        abort(404)

    return jsonify(dict(payout))


@payouts_bp.route("/<int:payout_id>/approve", methods=["POST"])
def approve_payout(payout_id):
    """Approve a pending payout that belongs to the signed-in user."""
    user_id = current_user_id()
    db = get_db()

    payout = db.execute(
        "SELECT p.id, p.status, a.user_id AS owner_id "
        "FROM payouts p JOIN accounts a ON a.id = p.account_id "
        "WHERE p.id = ?",
        (payout_id,),
    ).fetchone()
    if payout is None:
        abort(404)
    if payout["owner_id"] != user_id:
        abort(403)
    if payout["status"] != "pending":
        abort(409, "Payout is not awaiting approval.")

    try:
        db.execute(
            "UPDATE payouts SET status = 'approved' WHERE id = ?",
            (payout_id,),
        )
        db.commit()
    except Exception:
        db.rollback()
        abort(500, "Could not approve the payout.")

    return redirect(url_for("payouts.view_payout", payout_id=payout_id))


@payouts_bp.route("/export")
def export_payouts():
    """Export the signed-in user's payouts as a CSV attachment."""
    user_id = current_user_id()
    status = request.args.get("status")
    try:
        limit = min(int(request.args.get("limit", "100")), 500)
    except ValueError:
        limit = 100

    db = get_db()
    if status:
        rows = db.execute(
            "SELECT p.id, p.amount_cents, p.status, p.created_at, e.name "
            "FROM payouts p "
            "JOIN accounts a ON a.id = p.account_id "
            "JOIN payees e ON e.id = p.payee_id "
            "WHERE a.user_id = ? AND p.status = ? "
            "ORDER BY p.created_at DESC LIMIT ?",
            (user_id, status, limit),
        ).fetchall()
    else:
        rows = db.execute(
            "SELECT p.id, p.amount_cents, p.status, p.created_at, e.name "
            "FROM payouts p "
            "JOIN accounts a ON a.id = p.account_id "
            "JOIN payees e ON e.id = p.payee_id "
            "WHERE a.user_id = ? "
            "ORDER BY p.created_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()

    csv_lines = ["id,payee,amount,status,created_at"]
    for row in rows:
        amount = "%.2f" % (row["amount_cents"] / 100)
        payee = row["name"].replace(",", " ")
        csv_lines.append(
            str(row["id"]) + "," + payee + "," + amount + ","
            + row["status"] + "," + row["created_at"]
        )
    body = "\n".join(csv_lines)

    return Response(
        body,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=payouts.csv"},
    )
