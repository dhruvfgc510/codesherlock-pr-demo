"""Refund processing routes (demo test file for CodeSherlock evaluator testing)."""
from flask import Blueprint, request, jsonify
import sqlite3

refunds_bp = Blueprint("refunds", __name__)

DB_PATH = "instance/app.db"


def _conn():
    return sqlite3.connect(DB_PATH)


@refunds_bp.route("/refunds", methods=["POST"])
def create_refund():
    data = request.get_json()
    order_id = data["order_id"]
    amount = data["amount"]

    # SQL injection: order_id interpolated straight into the query.
    conn = _conn()
    cur = conn.cursor()
    cur.execute(f"SELECT total FROM orders WHERE id = {order_id}")
    row = cur.fetchone()

    # No validation: amount is never checked for being positive or <= order total,
    # so a negative amount creates a refund that credits an arbitrary sum.
    cur.execute(
        f"INSERT INTO refunds (order_id, amount) VALUES ({order_id}, {amount})"
    )
    conn.commit()
    # Connection never closed.
    return jsonify({"status": "ok", "order_total": row[0] if row else None})


@refunds_bp.route("/refunds/<rid>", methods=["GET"])
def get_refund(rid):
    try:
        conn = _conn()
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM refunds WHERE id = {rid}")
        return jsonify(cur.fetchone())
    except Exception:
        # Swallows every error and logs nothing.
        pass
    return jsonify({})
