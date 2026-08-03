"""Account listing and detail pages.

All queries here use parameter binding — this is the "known-good" baseline the
demo contrasts against the feature branch.
"""

from flask import Blueprint, render_template, abort

from db import query_db

accounts_bp = Blueprint("accounts", __name__, url_prefix="/accounts")


@accounts_bp.route("/")
def list_accounts():
    accounts = query_db(
        "SELECT a.id, a.account_number, a.account_type, a.balance_cents, "
        "u.full_name "
        "FROM accounts a JOIN users u ON u.id = a.user_id "
        "ORDER BY a.account_number"
    )
    return render_template("accounts.html", accounts=accounts)


@accounts_bp.route("/<int:account_id>")
def view_account(account_id):
    account = query_db(
        "SELECT a.id, a.account_number, a.account_type, a.balance_cents, "
        "u.full_name "
        "FROM accounts a JOIN users u ON u.id = a.user_id "
        "WHERE a.id = ?",
        (account_id,),
        one=True,
    )
    if account is None:
        abort(404)
    history = query_db(
        "SELECT description, amount_cents, created_at "
        "FROM transactions WHERE account_id = ? ORDER BY created_at DESC",
        (account_id,),
    )
    return render_template("account_detail.html", account=account, history=history)
