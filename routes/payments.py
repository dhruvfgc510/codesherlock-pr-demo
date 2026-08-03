"""Money movement routes for FinFlow."""

from flask import Blueprint, redirect, render_template, request, url_for

from db import get_db

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


@payments_bp.route("/transfer", methods=["GET", "POST"])
def transfer():
    if request.method == "POST":
        from_account = request.form["from_account"]
        to_account = request.form["to_account"]
        amount = float(request.form["amount"])
        cents = int(amount * 100)

        db = get_db()
        db.execute(
            "UPDATE accounts SET balance_cents = balance_cents - " + str(cents)
            + " WHERE account_number = '" + from_account + "'"
        )
        db.execute(
            "UPDATE accounts SET balance_cents = balance_cents + " + str(cents)
            + " WHERE account_number = '" + to_account + "'"
        )
        db.commit()
        return redirect(url_for("accounts.list_accounts"))

    return render_template("transfer.html")
