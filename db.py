"""SQLite access helpers for FinFlow.

A single connection is created per request and stored on Flask's ``g`` object,
then closed automatically when the request ends.
"""

import sqlite3

from flask import current_app, g


def get_db():
    """Return the request-scoped SQLite connection, opening one if needed."""
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exception=None):
    """Close the request-scoped connection if it was opened."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def query_db(query, args=(), one=False):
    """Run a SELECT and return all rows, or a single row when ``one`` is True."""
    cur = get_db().execute(query, args)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


def init_db():
    """Create the tables and load the seed data from ``schema.sql``."""
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))
    db.commit()


def init_app(app):
    """Wire the teardown handler into the Flask app."""
    app.teardown_appcontext(close_db)
