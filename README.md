# FinFlow

A small fintech dashboard built with Flask + SQLite. It lists customer accounts,
balances, and recent transactions. This repository is used to demonstrate
CodeSherlock PR reviews.

## Requirements

- Python 3.10+

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Initialize the database

Creates the tables and loads the seed data:

```bash
flask --app app init-db
```

## Run

```bash
flask --app app run --debug
```

Then open http://127.0.0.1:5000.

## Project layout

```
app.py                 # Flask app factory, config, init-db command
db.py                  # SQLite connection + query helpers
schema.sql             # Tables + seed data
routes/
  home.py              # Dashboard (totals + recent activity)
  accounts.py          # Account list + detail
templates/             # Jinja templates
static/style.css       # Styling
```
