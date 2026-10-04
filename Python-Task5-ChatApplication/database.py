import sqlite3
import hashlib
from datetime import datetime


DATABASE_NAME = "chat_app.db"


def get_connection():
    """Create and return a database connection."""
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def hash_password(password):
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def initialize_database():
    """Create all required database tables."""
    connection = get_connection()
    cursor = connection.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Chat rooms table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            room_name TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    # Create default room
    cursor.execute("""
        INSERT OR IGNORE INTO rooms (name, created_at)
        VALUES (?, ?)
    """, ("General", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    connection.commit()
    connection.close()


def register_user(username, password):
    """Register a new user."""
    username = username.strip()

    if not username or not password:
        return False, "Username and password are required."

    if len(username) < 3:
        return False, "Username must contain at least 3 characters."

    if len(password) < 4:
        return False, "Password must contain at least 4 characters."

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO users (username, password_hash, created_at)
            VALUES (?, ?, ?)
        """, (
            username,
            hash_password(password),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        connection.commit()
        return True, "Registration successful."

    except sqlite3.IntegrityError:
        return False, "Username already exists."

    finally:
        connection.close()


def verify_login(username, password):
    """Verify username and password."""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT password_hash
        FROM users
        WHERE username = ?
    """, (username.strip(),))

    user = cursor.fetchone()
    connection.close()

    if user is None:
        return False

    return user["password_hash"] == hash_password(password)


def create_room(room_name):
    """Create a new chat room."""
    room_name = room_name.strip()

    if not room_name:
        return False, "Room name cannot be empty."

    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("""
            INSERT INTO rooms (name, created_at)
            VALUES (?, ?)
        """, (
            room_name,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        connection.commit()
        return True, "Room created successfully."

    except sqlite3.IntegrityError:
        return False, "Room already exists."

    finally:
        connection.close()


def get_rooms():
    """Return all available chat rooms."""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT name
        FROM rooms
        ORDER BY name
    """)

    rooms = [row["name"] for row in cursor.fetchall()]

    connection.close()

    return rooms


def save_message(username, room_name, message):
    """Save a chat message to the database."""
    connection = get_connection()
    cursor = connection.cursor()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO messages
        (username, room_name, message, timestamp)
        VALUES (?, ?, ?, ?)
    """, (
        username,
        room_name,
        message,
        timestamp
    ))

    connection.commit()
    connection.close()

    return timestamp


def get_message_history(room_name, limit=100):
    """Return recent messages from a chat room."""
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT username, message, timestamp
        FROM messages
        WHERE room_name = ?
        ORDER BY id DESC
        LIMIT ?
    """, (room_name, limit))

    messages = cursor.fetchall()

    connection.close()

    # Return oldest → newest
    return list(reversed(messages))


if __name__ == "__main__":
    initialize_database()
    print("Database initialized successfully.")