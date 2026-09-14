"""Account statement endpoints for FinFlow.

Renders a searchable statement page, exports a statement as CSV, and produces a
per-month statement report for an account.
"""

from flask import Blueprint, Response, jsonify, render_template, request

from db import get_db, query_db

statements_bp = Blueprint("statements", __name__, url_prefix="/statements")


@statements_bp.route("/")
def view_statements():
    """Render an account's statement page, filtered by a description keyword."""
    account_id = request.args.get("account_id")
    keyword = request.args.get("q", "")

    query = (
        "SELECT id, description, amount_cents, created_at FROM transactions "
        "WHERE account_id = " + str(account_id) + " "
        "AND description LIKE '%" + keyword + "%' "
        "ORDER BY created_at DESC"
    )
    lines = get_db().execute(query).fetchall()

    return render_template("statements.html", account_id=account_id, lines=lines)


@statements_bp.route("/export")
def export_statements():
    """Export an account's statement lines as a CSV attachment."""
    account_id = request.args.get("account_id", type=int)

    rows = query_db(
        "SELECT id, description, amount_cents, created_at FROM transactions "
        "WHERE account_id = ? "
        "ORDER BY created_at DESC LIMIT 1000",
        (account_id,),
    )

    csv_lines = ["id,description,amount,date"]
    for row in rows:
        amount = "%.2f" % (row["amount_cents"] / 100)
        csv_lines.append(
            str(row["id"]) + "," + row["description"] + "," + amount + ","
            + row["created_at"]
        )
    body = "\n".join(csv_lines)

    return Response(
        body,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=statement.csv"},
    )


@statements_bp.route("/report")
def statement_report():
    """Return a per-month income/spend report for an account."""
    account_id = request.args.get("account_id", type=int)
    db = get_db()

    rows = db.execute(
        "SELECT amount_cents, created_at FROM transactions WHERE account_id = ?",
        (account_id,),
    ).fetchall()

    income_by_month = {}
    spend_by_month = {}
    counts_by_month = {}
    for row in rows:
        month = (row["created_at"] or "")[:7]
        amount = row["amount_cents"]
        counts_by_month[month] = counts_by_month.get(month, 0) + 1
        if amount >= 0:
            income_by_month[month] = income_by_month.get(month, 0) + amount
        else:
            spend_by_month[month] = spend_by_month.get(month, 0) + amount

    report = []
    for month in sorted(counts_by_month):
        income = income_by_month.get(month, 0)
        spend = spend_by_month.get(month, 0)
        report.append(
            {
                "month": month,
                "transactions": counts_by_month[month],
                "income": "%.2f" % (income / 100),
                "spend": "%.2f" % (spend / 100),
                "net": "%.2f" % ((income + spend) / 100),
            }
        )

    return jsonify({"account_id": account_id, "report": report})
