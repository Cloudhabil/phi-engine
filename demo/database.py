"""
phi_engine.demo.database — SQLite ORM for demo analytics.

Pattern from sovereign-pio/docs/usecases/demos/demo_database.py.
5 tables: sessions, analyses, transforms, payments, user_metadata.
"""
from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

DB_PATH = os.environ.get("PHI_ENGINE_DB", "phi_engine_demo.db")

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS demo_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    customer_email TEXT,
    company_name TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    total_transforms INTEGER DEFAULT 0,
    total_analyses INTEGER DEFAULT 0,
    mode TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_email ON demo_sessions(customer_email);

CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    adapter TEXT NOT NULL,
    input_data TEXT,
    consistency_score REAL,
    recommendations TEXT,
    metadata TEXT,
    FOREIGN KEY(session_id) REFERENCES demo_sessions(session_id)
);
CREATE INDEX IF NOT EXISTS idx_analyses_session ON analyses(session_id);

CREATE TABLE IF NOT EXISTS transforms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    mode TEXT NOT NULL,
    n_values INTEGER,
    metadata TEXT,
    FOREIGN KEY(session_id) REFERENCES demo_sessions(session_id)
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    stripe_session_id TEXT UNIQUE NOT NULL,
    customer_email TEXT NOT NULL,
    plan_id TEXT NOT NULL,
    plan_name TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    billing_type TEXT NOT NULL,
    payment_status TEXT DEFAULT 'pending',
    paid_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    FOREIGN KEY(session_id) REFERENCES demo_sessions(session_id)
);
CREATE INDEX IF NOT EXISTS idx_payments_email ON payments(customer_email);

CREATE TABLE IF NOT EXISTS user_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_email TEXT UNIQUE NOT NULL,
    transforms_today INTEGER DEFAULT 0,
    analyses_today INTEGER DEFAULT 0,
    total_transforms INTEGER DEFAULT 0,
    total_analyses INTEGER DEFAULT 0,
    last_reset_date TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class DemoDatabase:
    """SQLite ORM for phi-engine demo analytics."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or DB_PATH
        self._init_db()

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(DB_SCHEMA)

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Sessions
    # ------------------------------------------------------------------
    def create_session(
        self,
        session_id: str,
        email: str | None = None,
        company: str | None = None,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO demo_sessions "
                "(session_id, customer_email, company_name) VALUES (?, ?, ?)",
                (session_id, email, company),
            )

    def end_session(self, session_id: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE demo_sessions SET ended_at = CURRENT_TIMESTAMP "
                "WHERE session_id = ?",
                (session_id,),
            )

    # ------------------------------------------------------------------
    # Analyses
    # ------------------------------------------------------------------
    def log_analysis(
        self,
        session_id: str,
        adapter: str,
        input_data: dict,
        consistency_score: float,
        recommendations: list[str],
        metadata: dict | None = None,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO analyses "
                "(session_id, adapter, input_data, consistency_score, "
                "recommendations, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    adapter,
                    json.dumps(input_data),
                    consistency_score,
                    json.dumps(recommendations),
                    json.dumps(metadata or {}),
                ),
            )
            conn.execute(
                "UPDATE demo_sessions SET total_analyses = total_analyses + 1 "
                "WHERE session_id = ?",
                (session_id,),
            )

    # ------------------------------------------------------------------
    # Transforms
    # ------------------------------------------------------------------
    def log_transform(
        self,
        session_id: str,
        mode: str,
        n_values: int,
        metadata: dict | None = None,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO transforms "
                "(session_id, mode, n_values, metadata) VALUES (?, ?, ?, ?)",
                (session_id, mode, n_values, json.dumps(metadata or {})),
            )
            conn.execute(
                "UPDATE demo_sessions SET total_transforms = total_transforms + 1 "
                "WHERE session_id = ?",
                (session_id,),
            )

    # ------------------------------------------------------------------
    # Payments
    # ------------------------------------------------------------------
    def log_payment_initiated(
        self,
        session_id: str,
        stripe_session_id: str,
        customer_email: str,
        plan_id: str,
        plan_name: str,
        amount_cents: int,
        billing_type: str,
        metadata: dict | None = None,
    ) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO payments "
                "(session_id, stripe_session_id, customer_email, plan_id, "
                "plan_name, amount_cents, billing_type, metadata) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id,
                    stripe_session_id,
                    customer_email,
                    plan_id,
                    plan_name,
                    amount_cents,
                    billing_type,
                    json.dumps(metadata or {}),
                ),
            )

    def update_payment_status(self, stripe_session_id: str, status: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE payments SET payment_status = ?, "
                "paid_at = CASE WHEN ? = 'completed' THEN CURRENT_TIMESTAMP ELSE paid_at END "
                "WHERE stripe_session_id = ?",
                (status, status, stripe_session_id),
            )

    def has_paid_access(self, session_id: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM payments "
                "WHERE session_id = ? AND payment_status = 'completed'",
                (session_id,),
            ).fetchone()
            return row[0] > 0 if row else False

    # ------------------------------------------------------------------
    # User metadata / rate limiting
    # ------------------------------------------------------------------
    def get_or_create_user(self, email: str) -> dict:
        today = datetime.now().strftime("%Y-%m-%d")
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM user_metadata WHERE customer_email = ?",
                (email,),
            ).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO user_metadata "
                    "(customer_email, last_reset_date) VALUES (?, ?)",
                    (email, today),
                )
                return {
                    "email": email,
                    "transforms_today": 0,
                    "analyses_today": 0,
                    "total_transforms": 0,
                    "total_analyses": 0,
                }
            user = dict(row)
            if user.get("last_reset_date") != today:
                conn.execute(
                    "UPDATE user_metadata SET transforms_today = 0, "
                    "analyses_today = 0, last_reset_date = ?, "
                    "updated_at = CURRENT_TIMESTAMP WHERE customer_email = ?",
                    (today, email),
                )
                user["transforms_today"] = 0
                user["analyses_today"] = 0
            return user

    def increment_usage(self, email: str, transforms: int = 0, analyses: int = 0) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE user_metadata SET "
                "transforms_today = transforms_today + ?, "
                "analyses_today = analyses_today + ?, "
                "total_transforms = total_transforms + ?, "
                "total_analyses = total_analyses + ?, "
                "updated_at = CURRENT_TIMESTAMP "
                "WHERE customer_email = ?",
                (transforms, analyses, transforms, analyses, email),
            )

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------
    def get_session_stats(self, session_id: str) -> dict:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT total_transforms, total_analyses FROM demo_sessions "
                "WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            return dict(row) if row else {}

    def get_all_stats(self) -> dict:
        with self._conn() as conn:
            sessions = conn.execute("SELECT COUNT(*) FROM demo_sessions").fetchone()[0]
            analyses = conn.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
            transforms = conn.execute("SELECT COUNT(*) FROM transforms").fetchone()[0]
            payments = conn.execute(
                "SELECT COUNT(*) FROM payments WHERE payment_status = 'completed'"
            ).fetchone()[0]
            return {
                "total_sessions": sessions,
                "total_analyses": analyses,
                "total_transforms": transforms,
                "paid_users": payments,
            }

    def get_revenue_stats(self) -> dict:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(amount_cents), 0) as total_cents, "
                "COUNT(*) as n_payments "
                "FROM payments WHERE payment_status = 'completed'"
            ).fetchone()
            total_cents = row[0]
            n_payments = row[1]
            return {
                "total_revenue_usd": total_cents / 100,
                "n_payments": n_payments,
            }
