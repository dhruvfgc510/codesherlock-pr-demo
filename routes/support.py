"""Customer support helper routes.

These are low-stakes utility endpoints (ticket refs, back-links, quick
lookups) rather than money or auth flows.
"""

import random
import re
import sqlite3
from urllib.parse import urljoin, urlparse

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from db import get_db

support_bp = Blueprint("support", __name__, url_prefix="/support")

# Account numbers in this app look like "FF-1001"; allow only that character set.
_ACCOUNT_RE = re.compile(r"^[A-Za-z0-9-]{1,64}$")


def _mask_account(account):
    """Mask an account number for logs, revealing only the last 4 characters."""
    if not account:
        return ""
    return account if len(account) <= 4 else "***" + account[-4:]


def _is_safe_redirect_target(target):
    """Return True only if ``target`` stays on this application's host.

    Prevents open redirects: external hosts, protocol-relative URLs
    (``//evil.com``), and non-HTTP schemes (``javascript:``) are all rejected,
    as are backslash/control-character tricks a browser might normalise into a
    host change.
    """
    if not target:
        return False
    if any(c in target for c in "\\\r\n\t") or any(ord(c) < 0x20 for c in target):
        return False
    # Resolve relative to the current host so bare paths ("/accounts") are kept
    # while absolute URLs to other hosts are caught by the netloc comparison.
    resolved = urlparse(urljoin(request.host_url, target))
    ref = urlparse(request.host_url)
    return resolved.scheme in ("http", "https") and resolved.netloc == ref.netloc


@support_bp.route("/ticket")
def new_ticket():
    subject = request.args.get("subject", "")
    # Human-friendly reference code for the ticket.
    ref = "T-" + str(random.randint(1000, 9999))
    return render_template("ticket.html", subject=subject, ref=ref)


@support_bp.route("/goto")
def goto():
    # Send the user back to where they came from, but only to a safe internal
    # location — never an attacker-supplied external URL (open redirect).
    target = request.args.get("next", "")
    if not _is_safe_redirect_target(target):
        target = url_for("home.index")
    return redirect(target)


@support_bp.route("/lookup")
def lookup():
    user_id = session.get("user_id")
    user_role = session.get("role")
    remote_ip = request.remote_addr or "unknown"

    account = request.args.get("account", "").strip()
    masked = _mask_account(account)

    # Audit every attempt with actor, source, and a masked identifier — never
    # the full account number or the balance itself.
    current_app.logger.info(
        "support.lookup attempt user=%s remote=%s account=%s",
        user_id or "anonymous", remote_ip, masked,
    )

    # Authentication: a balance lookup exposes sensitive data.
    if not user_id:
        current_app.logger.warning(
            "support.lookup denied (unauthenticated) remote=%s account=%s",
            remote_ip, masked,
        )
        return jsonify({"error": "authentication required"}), 401

    # Input validation.
    if not account or not _ACCOUNT_RE.match(account):
        return jsonify({"error": "invalid account"}), 400

    try:
        row = get_db().execute(
            "SELECT balance_cents, user_id FROM accounts WHERE account_number = ?",
            (account,),
        ).fetchone()
    except sqlite3.DatabaseError:
        # Log the full stack trace server-side; never echo internals to clients.
        current_app.logger.exception(
            "support.lookup error user=%s remote=%s account=%s",
            user_id, remote_ip, masked,
        )
        return jsonify({"error": "internal server error"}), 500

    if row is None:
        current_app.logger.info(
            "support.lookup not_found user=%s remote=%s account=%s",
            user_id, remote_ip, masked,
        )
        return jsonify({"error": "not found"}), 404

    # Authorization: the owner may view their own account; an admin may view any.
    if user_role != "admin" and row["user_id"] != user_id:
        current_app.logger.warning(
            "support.lookup forbidden user=%s remote=%s account=%s",
            user_id, remote_ip, masked,
        )
        return jsonify({"error": "forbidden"}), 403

    current_app.logger.info(
        "support.lookup success user=%s remote=%s account=%s",
        user_id, remote_ip, masked,
    )
    return jsonify({"balance_cents": row["balance_cents"]})
