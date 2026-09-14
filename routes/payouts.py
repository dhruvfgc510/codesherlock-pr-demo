"""Payout endpoints for FinFlow.

Exposes approval of a pending payout, a CSV export of an account's payouts,
and a per-payee summary.
"""

from flask import Blueprint, Response, abort, jsonify, request

from db import get_db, query_db

payouts_bp = Blueprint("payouts", __name__, url_prefix="/payouts")


@payouts_bp.route("/<int:payout_id>/approve", methods=["POST"])
def approve_payout(payout_id):
    """Approve a pending payout."""
    payout = query_db(
        "SELECT id, status FROM payouts WHERE id = ?",
        (payout_id,),
        one=True,
    )
    if payout is None:
        abort(404)
    if payout["status"] != "pending":
        abort(409, "Payout is not awaiting approval.")

    db = get_db()
    db.execute(
        "UPDATE payouts SET status = 'approved' WHERE id = ?",
        (payout_id,),
    )
    db.commit()

    return jsonify({"id": payout_id, "status": "approved"})


@payouts_bp.route("/export")
def export_payouts():
    """Export an account's payouts as a CSV attachment."""
    account_id = request.args.get("account_id", type=int)

    rows = query_db(
        "SELECT p.id, p.amount_cents, p.status, p.created_at, e.name "
        "FROM payouts p JOIN payees e ON e.id = p.payee_id "
        "WHERE p.account_id = ? "
        "ORDER BY p.created_at DESC LIMIT 500",
        (account_id,),
    )

    csv_lines = ["id,payee,amount,status,created_at"]
    for row in rows:
        amount = "%.2f" % (row["amount_cents"] / 100)
        csv_lines.append(
            str(row["id"]) + "," + row["name"] + "," + amount + ","
            + row["status"] + "," + row["created_at"]
        )
    body = "\n".join(csv_lines)

    return Response(
        body,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=payouts.csv"},
    )


@payouts_bp.route("/summary")
def payout_summary():
    """Return a per-payee summary (count and total) of an account's payouts."""
    account_id = request.args.get("account_id", type=int)
    db = get_db()

    payouts = db.execute(
        "SELECT payee_id, amount_cents FROM payouts WHERE account_id = ?",
        (account_id,),
    ).fetchall()
    payees = db.execute("SELECT id, name FROM payees").fetchall()
    name_by_id = {row["id"]: row["name"] for row in payees}

    totals = {}
    counts = {}
    for payout in payouts:
        name = name_by_id.get(payout["payee_id"], "unknown")
        totals[name] = totals.get(name, 0) + payout["amount_cents"]
        counts[name] = counts.get(name, 0) + 1

    summary = []
    for name in totals:
        summary.append(
            {
                "payee": name,
                "count": counts[name],
                "total": "%.2f" % (totals[name] / 100),
            }
        )
    summary.sort(key=lambda item: item["payee"])

    return jsonify(summary)
