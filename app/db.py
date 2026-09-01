import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "ledger.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                raw_text TEXT NOT NULL,
                item TEXT NOT NULL,
                amount INTEGER NOT NULL,
                category TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS budgets (
                category TEXT PRIMARY KEY,
                monthly_amount INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS learned_categories (
                item_key TEXT PRIMARY KEY,
                category TEXT NOT NULL
            )
            """
        )


def insert_entry(raw_text: str, item: str, amount: int, category: str) -> None:
    created_at = datetime.now().isoformat(timespec="seconds")
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO entries (created_at, raw_text, item, amount, category) "
            "VALUES (?, ?, ?, ?, ?)",
            (created_at, raw_text, item, amount, category),
        )


def fetch_all_entries() -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM entries").fetchall()
    return [dict(row) for row in rows]


def fetch_recent_entries(limit: int = 10) -> List[Dict]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM entries ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(row) for row in rows]


def delete_entry(entry_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))


def update_entry_category(entry_id: int, category: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE entries SET category = ? WHERE id = ?", (category, entry_id)
        )


def get_entry(entry_id: int) -> Optional[Dict]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    return dict(row) if row else None


def get_learned_category(item_key: str) -> Optional[str]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT category FROM learned_categories WHERE item_key = ?", (item_key,)
        ).fetchone()
    return row["category"] if row else None


def set_learned_category(item_key: str, category: str) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO learned_categories (item_key, category) VALUES (?, ?)
            ON CONFLICT(item_key) DO UPDATE SET category = excluded.category
            """,
            (item_key, category),
        )


def get_budgets() -> Dict[str, int]:
    with get_connection() as conn:
        rows = conn.execute("SELECT category, monthly_amount FROM budgets").fetchall()
    return {row["category"]: row["monthly_amount"] for row in rows}


def set_budget(category: str, amount: int) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO budgets (category, monthly_amount) VALUES (?, ?)
            ON CONFLICT(category) DO UPDATE SET monthly_amount = excluded.monthly_amount
            """,
            (category, amount),
        )
