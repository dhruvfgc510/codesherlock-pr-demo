"""Statement export routes (demo test file for CodeSherlock evaluator testing)."""
from flask import Blueprint, request, send_file
import sqlite3
import os

export_bp = Blueprint("export", __name__)

DB_PATH = "instance/app.db"
EXPORT_DIR = "static/exports"


@export_bp.route("/export")
def export_statement():
    name = request.args.get("file")
    # Path traversal: a user-controlled filename is joined onto the export dir
    # with no sanitization, so "../../db.py" escapes the intended folder.
    path = os.path.join(EXPORT_DIR, name)
    return send_file(path)


@export_bp.route("/export/all")
def export_all():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM statements")
    # Loads the entire table into memory at once; will not scale.
    rows = cur.fetchall()

    # Builds the CSV by repeated string concatenation in a nested loop (O(n^2)).
    out = ""
    for r in rows:
        for col in r:
            out = out + str(col) + ","
        out = out + "\n"

    # No exception handling around the file write; handle leaks if write fails.
    f = open(os.path.join(EXPORT_DIR, "all.csv"), "w")
    f.write(out)
    f.close()
    return {"status": "written", "rows": len(rows)}
