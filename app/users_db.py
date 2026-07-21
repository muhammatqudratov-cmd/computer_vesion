# users_db.py
# Foydalanuvchilar (users) va ularning tarixi (history) uchun SQLite baza.
# Chroma vektor bazasi (database.py) instance-level "bu narsani ko'rganmiz-
# ganmi" solishtirish uchun, bu yerda esa relyatsion ma'lumotlar (login
# ma'lumotlari, tarix ro'yxati) saqlanadi - shu sabab alohida fayl/jadval.

import os
import sqlite3

_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app.db",
)


def _get_connection():
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _init_db():
    conn = _get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                object_name TEXT,
                guess_label TEXT,
                info_text TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()
    finally:
        conn.close()


_init_db()


def create_user(username: str, hashed_password: str) -> int:
    """Yangi foydalanuvchi yozuvini yaratadi, id'sini qaytaradi.
    Agar username band bo'lsa ValueError ko'taradi (chaqiruvchi buni
    HTTP 400'ga aylantiradi)."""
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO users (username, hashed_password) VALUES (?, ?)",
            (username, hashed_password),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError(f"Username allaqachon band: {username}")
    finally:
        conn.close()


def get_user_by_username(username: str):
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id: int):
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def add_history_entry(user_id: int, object_name: str, guess_label: str, info_text: str) -> int:
    conn = _get_connection()
    try:
        cursor = conn.execute(
            """INSERT INTO history (user_id, object_name, guess_label, info_text)
               VALUES (?, ?, ?, ?)""",
            (user_id, object_name, guess_label, info_text),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_history_for_user(user_id: int):
    """Berilgan foydalanuvchining tarixini eng yangisidan boshlab qaytaradi."""
    conn = _get_connection()
    try:
        rows = conn.execute(
            """SELECT * FROM history WHERE user_id = ?
               ORDER BY created_at DESC, id DESC""",
            (user_id,),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
