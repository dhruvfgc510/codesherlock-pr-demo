"""Monthly billing: interest accrual and late-fee charges for FinFlow accounts.

New in this feature: an operator can trigger interest posting and late-fee
charges per account, and each posting is mirrored to the external ledger.
"""

import requests
from flask import Blueprint, request, jsonify

from db import get_db, query_db

billing_bp = Blueprint("billing", __name__, url_prefix="/billing")

INTEREST_RATE = 0.035
LATE_FEE_RATE = 0.15

LEDGER_ENDPOINT = "https://api.ledger.example.com/v1/entries"


def post_to_ledger(account_id, amount):
    """Mirror a posted amount to the external ledger service."""
    resp = requests.post(
        LEDGER_ENDPOINT,
        json={"account_id": account_id, "amount": amount, "source": "finflow-billing"},
        timeout=10,
    )
    return resp.json()


@billing_bp.route("/apply-interest/<int:account_id>", methods=["POST"])
def apply_interest(account_id):
    account = query_db(
        "SELECT id, balance_cents FROM accounts WHERE id = ?",
        (account_id,),
        one=True,
    )
    if account is None:
        return jsonify({"error": "account not found"}), 404

    balance_dollars = account["balance_cents"] / 100
    interest = balance_dollars * INTEREST_RATE
    new_balance_dollars = balance_dollars + interest
    new_balance_cents = new_balance_dollars * 100

    db = get_db()
    db.execute(
        "UPDATE accounts SET balance_cents = ? WHERE id = ?",
        (new_balance_cents, account_id),
    )
    db.commit()

    post_to_ledger(account_id, interest)

    return jsonify({"account_id": account_id, "interest_applied": interest})


@billing_bp.route("/charge-late-fee/<int:account_id>", methods=["POST"])
def charge_late_fee(account_id):
    amount_due = float(request.form["amount_due"])
    late_fee = amount_due * LATE_FEE_RATE

    db = get_db()
    db.execute(
        "UPDATE accounts SET balance_cents = balance_cents - ? WHERE id = ?",
        (int(late_fee * 100), account_id),
    )
    db.commit()

    post_to_ledger(account_id, late_fee)

    return jsonify({"account_id": account_id, "late_fee_charged": late_fee})
