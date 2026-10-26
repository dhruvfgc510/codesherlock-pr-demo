"""Customer search routes (demo test file for CodeSherlock evaluator testing)."""
from flask import Blueprint, request, jsonify
import sqlite3

search_bp = Blueprint("search", __name__)

DB_PATH = "instance/app.db"


def run_query(sql):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(sql)
    return cur.fetchall()


def run_query_dict(sql):
    # Near-duplicate of run_query above: same connect/execute, only the row
    # shaping differs. Duplicated DB-access boilerplate.
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, r)) for r in rows]


@search_bp.route("/search")
def search_customers():
    term = request.args.get("q", "")
    # SQL injection: the search term is formatted directly into a LIKE clause.
    sql = f"SELECT * FROM customers WHERE name LIKE '%{term}%'"
    # No pagination or limit: every matching row is loaded and returned at once.
    results = run_query_dict(sql)
    return jsonify(results)


@search_bp.route("/search/count")
def search_count():
    term = request.args.get("q", "")
    # Same injection pattern repeated here.
    sql = f"SELECT COUNT(*) FROM customers WHERE name LIKE '%{term}%'"
    return jsonify({"count": run_query(sql)[0][0]})
