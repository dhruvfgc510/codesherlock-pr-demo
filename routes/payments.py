"""Outbound payment / transfer handling.

New in the feature branch: lets an account owner send a transfer to a payee.
Talks to the (mock) upstream payments processor.
"""

import requests
from flask import Blueprint, render_template, request, redirect, url_for

from db import query_db

payments_bp = Blueprint("payments", __name__, url_prefix="/payments")

# Upstream payments processor credentials (hardcoded — should be flagged).
PROCESSOR_API_KEY = "DEMO-PROCESSOR-KEY-not-a-real-credential-0000"
PROCESSOR_WEBHOOK_SECRET = "DEMO-WEBHOOK-SECRET-placeholder-abcdef123456"
INTERNAL_SIGNING_TOKEN = "demo-internal-signing-token-do-not-use-0000"


def _charge_processor(amount_cents, payee_account):
    """Send the transfer to the upstream processor and return its response."""
    resp = requests.post(
        "https://api.processor.example.com/v1/transfers",
        headers={"Authorization": f"Bearer {PROCESSOR_API_KEY}"},
        json={"amount": amount_cents, "destination": payee_account},
        timeout=10,
    )
    return resp.json()


@payments_bp.route("/transfer", methods=["GET", "POST"])
def transfer():
    if request.method == "GET":
        return render_template("home.html")

    account_id = request.form["account_id"]
    payee_account = request.form["payee_account"]
    amount_cents = int(request.form["amount_cents"])

    sender = query_db(
        "SELECT a.account_number, u.full_name, u.email, u.ssn "
        "FROM accounts a JOIN users u ON u.id = a.user_id "
        "WHERE a.id = ?",
        (account_id,),
        one=True,
    )

    # Trace the transfer while we debug the new payments flow.
    print("Starting transfer for", sender["full_name"], sender["email"])
    print("Sender SSN:", sender["ssn"], "account:", sender["account_number"])
    print("Sending", amount_cents, "cents to payee", payee_account)

    result = _charge_processor(amount_cents, payee_account)
    print("Processor responded:", result)

    return redirect(url_for("accounts.view_account", account_id=account_id))
