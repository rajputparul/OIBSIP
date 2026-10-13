from pathlib import Path
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "chat_app.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL COLLATE NOCASE UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                room TEXT NOT NULL DEFAULT 'General',
                message TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_messages_room_id
            ON messages(room, id);
        """)

        conn.execute(
            "INSERT OR IGNORE INTO rooms (name) VALUES (?)",
            ("General",)
        )

        conn.execute("""
            INSERT OR IGNORE INTO rooms (name)
            SELECT DISTINCT room FROM messages
        """)


def register_user(username, password):
    username = username.strip()

    if not 3 <= len(username) <= 24:
        return False, "Username must be 3–24 characters."

    if not username.replace("_", "").isalnum():
        return False, "Use only letters, numbers and underscores."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    password_hash = generate_password_hash(password)

    try:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
        return True, "Account created! You can log in now."
    except sqlite3.IntegrityError:
        return False, "That username is already taken."


def verify_login(username, password):
    with get_connection() as conn:
        user = conn.execute(
            "SELECT username, password_hash FROM users WHERE username = ?",
            (username.strip(),)
        ).fetchone()

    return bool(user and check_password_hash(user["password_hash"], password))


def create_room(name):
    name = name.strip()

    if not 1 <= len(name) <= 30:
        return False, "Room name must be 1–30 characters."

    if not all(c.isalnum() or c in " _-" for c in name):
        return False, "Use letters, numbers, spaces, underscores or hyphens."

    try:
        with get_connection() as conn:
            conn.execute("INSERT INTO rooms (name) VALUES (?)", (name,))
        return True, name
    except sqlite3.IntegrityError:
        with get_connection() as conn:
            existing = conn.execute(
                "SELECT name FROM rooms WHERE name = ?",
                (name,)
            ).fetchone()

        if existing:
            return False, "That room already exists."
        return False, "Could not create the room."


def get_recent_messages(room="General", limit=100):
    limit = max(1, min(int(limit), 100))

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT username, room, message, created_at
            FROM messages
            WHERE room = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (room, limit)
        ).fetchall()

    return [dict(row) for row in reversed(rows)]


def save_message(username, room, message):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO messages (username, room, message)
            VALUES (?, ?, ?)
            """,
            (username, room, message)
        )

        row = conn.execute(
            """
            SELECT username, room, message, created_at
            FROM messages WHERE id = ?
            """,
            (cursor.lastrowid,)
        ).fetchone()

    return dict(row)


def get_room_names():
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT name FROM rooms ORDER BY name COLLATE NOCASE"
        ).fetchall()

    return [row["name"] for row in rows]
