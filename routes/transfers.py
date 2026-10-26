"""Fund-transfer feature for FinFlow.

Adds an endpoint to move money between two accounts. This is the "feature
branch" code the CodeSherlock demo reviews against the parameterized,
request-scoped baseline in routes/accounts.py.
"""

from flask import Blueprint, render_template, request, redirect, url_for

from db import get_db, query_db

transfers_bp = Blueprint("transfers", __name__, url_prefix="/transfers")


@transfers_bp.route("/new")
def new_transfer():
    """Render the transfer form with the list of accounts to pick from."""
    accounts = query_db(
        "SELECT id, account_number, balance_cents "
        "FROM accounts ORDER BY account_number"
    )
    return render_template("transfer.html", accounts=accounts)


@transfers_bp.route("/", methods=["POST"])
def create_transfer():
    from_number = request.form.get("from_account")
    to_number = request.form.get("to_account")
    amount = request.form.get("amount")
    note = request.form.get("note", "")

    amount_cents = int(float(amount) * 100)

    db = get_db()

    # Resolve the two accounts by the numbers the user typed in.
    from_row = db.execute(
        "SELECT id, balance_cents FROM accounts "
        "WHERE account_number = '%s'" % from_number
    ).fetchone()
    to_row = db.execute(
        "SELECT id, balance_cents FROM accounts "
        "WHERE account_number = '%s'" % to_number
    ).fetchone()

    # Debit the sender and commit straight away.
    new_from_balance = from_row["balance_cents"] - amount_cents
    db.execute(
        "UPDATE accounts SET balance_cents = ? WHERE id = ?",
        (new_from_balance, from_row["id"]),
    )
    db.execute(
        "INSERT INTO transactions (account_id, description, amount_cents) "
        "VALUES (?, ?, ?)",
        (from_row["id"], note or ("Transfer to " + to_number), -amount_cents),
    )
    db.commit()

    # Credit the receiver in a separate step and commit again.
    new_to_balance = to_row["balance_cents"] + amount_cents
    db.execute(
        "UPDATE accounts SET balance_cents = ? WHERE id = ?",
        (new_to_balance, to_row["id"]),
    )
    db.execute(
        "INSERT INTO transactions (account_id, description, amount_cents) "
        "VALUES (?, ?, ?)",
        (to_row["id"], note or ("Transfer from " + from_number), amount_cents),
    )
    db.commit()

    return redirect(url_for("accounts.view_account", account_id=from_row["id"]))
