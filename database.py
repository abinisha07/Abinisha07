import os
import sqlite3
from contextlib import contextmanager

from dotenv import load_dotenv

load_dotenv()


# --------------------------------------------------
# DATABASE SETTINGS
# --------------------------------------------------

DB_PATH = os.getenv(
    "DATABASE_URL",
    "sqlite:///./pocketsmart.db"
).replace(
    "sqlite:///",
    ""
)


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

@contextmanager
def get_db():
    """
    Create a SQLite database connection.
    """

    conn = sqlite3.connect(DB_PATH)

    # Return rows like dictionaries
    conn.row_factory = sqlite3.Row

    try:
        yield conn
        conn.commit()

    finally:
        conn.close()


# --------------------------------------------------
# INITIALIZE DATABASE
# --------------------------------------------------

def init_db():
    """
    Create required database tables.
    """

    with get_db() as db:

        # Users table
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Recommendations table
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                request_json TEXT NOT NULL,
                response_text TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY(user_id)
                REFERENCES users(id)
            )
            """
        )


# --------------------------------------------------
# CREATE USER
# --------------------------------------------------

def create_user(
    name,
    email,
    password_hash
):
    """
    Add a new user to the database.
    """

    with get_db() as db:

        cursor = db.execute(
            """
            INSERT INTO users
            (name, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (
                name,
                email.lower().strip(),
                password_hash
            )
        )

        return cursor.lastrowid


# --------------------------------------------------
# GET USER BY EMAIL
# --------------------------------------------------

def get_user_by_email(email):
    """
    Find a user using their email address.
    """

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (
                email.lower().strip(),
            )
        ).fetchone()


# --------------------------------------------------
# GET USER BY ID
# --------------------------------------------------

def get_user_by_id(user_id):
    """
    Find a user using their ID.
    """

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM users
            WHERE id = ?
            """,
            (
                user_id,
            )
        ).fetchone()


# --------------------------------------------------
# SAVE RECOMMENDATION
# --------------------------------------------------

def save_recommendation(
    user_id,
    category,
    request_json,
    response_text
):
    """
    Save an AI recommendation
    to the database.
    """

    import json

    with get_db() as db:

        cursor = db.execute(
            """
            INSERT INTO recommendations
            (
                user_id,
                category,
                request_json,
                response_text
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                user_id,
                category,
                json.dumps(request_json),
                response_text
            )
        )

        return cursor.lastrowid


# --------------------------------------------------
# GET RECOMMENDATION HISTORY
# --------------------------------------------------

def get_history(user_id):
    """
    Get all recommendations
    belonging to a particular user.
    """

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM recommendations
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (
                user_id,
            )
        ).fetchall()