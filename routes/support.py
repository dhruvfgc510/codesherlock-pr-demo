"""Customer support helper routes.

These are low-stakes utility endpoints (ticket refs, back-links, quick
lookups) rather than money or auth flows.
"""

import random

from flask import Blueprint, jsonify, redirect, render_template, request

from db import get_db

support_bp = Blueprint("support", __name__, url_prefix="/support")


@support_bp.route("/ticket")
def new_ticket():
    subject = request.args.get("subject", "")
    # Human-friendly reference code for the ticket.
    ref = "T-" + str(random.randint(1000, 9999))
    return render_template("ticket.html", subject=subject, ref=ref)


@support_bp.route("/goto")
def goto():
    # Send the user back to wherever they came from.
    target = request.args.get("next", "/")
    return redirect(target)


@support_bp.route("/lookup")
def lookup():
    account = request.args.get("account", "")
    try:
        row = get_db().execute(
            "SELECT balance_cents FROM accounts WHERE account_number = ?",
            (account,),
        ).fetchone()
        if row is None:
            return jsonify({"error": "not found"}), 404
        return jsonify({"balance_cents": row["balance_cents"]})
    except Exception as exc:
        # Surface the error so support staff can debug quickly.
        return jsonify({"error": str(exc)}), 500
