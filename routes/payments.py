"""Money movement routes for FinFlow."""

from decimal import Decimal, InvalidOperation

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.exceptions import HTTPException

from db import get_db

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


@payments_bp.route("/transfer", methods=["GET", "POST"])
def transfer():
    if request.method == "POST":
        # Authentication: only a logged-in user may move money.
        user_id = session.get("user_id")
        if not user_id:
            abort(401)

        # Validate and parse input before touching the database.
        from_account = request.form.get("from_account", "").strip()
        to_account = request.form.get("to_account", "").strip()
        try:
            amount = Decimal(request.form.get("amount", "0"))
        except (InvalidOperation, TypeError):
            flash("Invalid amount.")
            return render_template("transfer.html"), 400

        if not from_account or not to_account or amount <= 0:
            flash("Invalid transfer parameters.")
            return render_template("transfer.html"), 400

        cents = int((amount * 100).to_integral_value())

        db = get_db()
        try:
            # Authorization: the current user must own the source account.
            source = db.execute(
                "SELECT user_id, balance_cents FROM accounts "
                "WHERE account_number = ?",
                (from_account,),
            ).fetchone()
            if source is None:
                flash("Source account not found.")
                return render_template("transfer.html"), 404
            if source["user_id"] != user_id:
                abort(403)

            # Debit the source only if it still has sufficient funds. Keeping
            # the balance check in the WHERE clause means a concurrent transfer
            # cannot drive the balance negative between read and write.
            debit = db.execute(
                "UPDATE accounts SET balance_cents = balance_cents - ? "
                "WHERE account_number = ? AND balance_cents >= ?",
                (cents, from_account, cents),
            )
            if debit.rowcount == 0:
                db.rollback()
                flash("Insufficient funds.")
                return render_template("transfer.html"), 400

            # Credit the destination; fail the whole transfer if it is missing.
            credit = db.execute(
                "UPDATE accounts SET balance_cents = balance_cents + ? "
                "WHERE account_number = ?",
                (cents, to_account),
            )
            if credit.rowcount == 0:
                db.rollback()
                flash("Destination account not found.")
                return render_template("transfer.html"), 404

            db.commit()
            return redirect(url_for("accounts.list_accounts"))
        except HTTPException:
            # abort(...) responses must propagate unchanged, not be turned
            # into a generic 500 by the handler below.
            raise
        except Exception:
            # Roll back on any error so a partial transfer is never persisted,
            # and log server-side without leaking internals to the client.
            db.rollback()
            current_app.logger.exception(
                "Transfer failed for %s -> %s (%d cents)",
                from_account,
                to_account,
                cents,
            )
            flash("Transfer failed, please try again later.")
            return render_template("transfer.html"), 500

    return render_template("transfer.html")
