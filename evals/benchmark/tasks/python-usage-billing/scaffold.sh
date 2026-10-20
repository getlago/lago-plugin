#!/usr/bin/env bash
# Acme AI: a small standard-library Python app with one billable LLM action and no billing.
# The benchmark scorer imports app/db.py and billing.py from the finished workspace.
set -euo pipefail
mkdir -p app
cat > README.md <<'MD'
# Acme AI

Summarization API. Workspaces call `app.main.generate`, which runs a model and stores a generation row.
Python 3.9+, standard library only.
MD
touch app/__init__.py
cat > app/db.py <<'PY'
import os
import sqlite3
import uuid
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS workspaces (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL, plan TEXT NOT NULL DEFAULT 'free'
);
CREATE TABLE IF NOT EXISTS generations (
  id TEXT PRIMARY KEY, workspace_id TEXT NOT NULL REFERENCES workspaces(id), model TEXT NOT NULL,
  input_tokens INTEGER NOT NULL, output_tokens INTEGER NOT NULL, created_at TEXT NOT NULL
);
"""


def connect():
    conn = sqlite3.connect(os.environ.get("ACME_DB_PATH", "acme.db"))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with connect() as conn:
        conn.executescript(SCHEMA)


def create_workspace(workspace_id, name, email, plan="pro"):
    with connect() as conn:
        conn.execute("INSERT INTO workspaces (id, name, email, plan) VALUES (?, ?, ?, ?)", (workspace_id, name, email, plan))


def create_generation(workspace_id, model, input_tokens, output_tokens, created_at=None):
    generation_id = uuid.uuid4().hex
    created_at = created_at or datetime.now(timezone.utc)
    with connect() as conn:
        conn.execute(
            "INSERT INTO generations (id, workspace_id, model, input_tokens, output_tokens, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (generation_id, workspace_id, model, input_tokens, output_tokens, created_at.isoformat()),
        )
    return generation_id


def get_generation(generation_id):
    with connect() as conn:
        row = conn.execute("SELECT * FROM generations WHERE id = ?", (generation_id,)).fetchone()
    return dict(row) if row else None
PY
cat > app/llm.py <<'PY'
def summarize(text):
    """Stand-in for the model provider call."""
    return {"summary": text[:80], "model": "acme-small", "usage": {"input_tokens": max(1, len(text) // 4), "output_tokens": 20}}
PY
cat > app/main.py <<'PY'
from app import db, llm


def generate(workspace_id, text):
    result = llm.summarize(text)
    usage = result["usage"]
    db.create_generation(workspace_id, result["model"], usage["input_tokens"], usage["output_tokens"])
    return result["summary"]
PY
