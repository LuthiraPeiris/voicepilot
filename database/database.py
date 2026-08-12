import sqlite3
from pathlib import Path


DATABASE_PATH = Path("database") / "voicepilot.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)

    return connection


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            path TEXT NOT NULL UNIQUE
        )
        """
    )

    connection.commit()
    connection.close()


def clear_folders():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM folders")

    connection.commit()
    connection.close()


def add_folder(name, path):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO folders (name, path)
        VALUES (?, ?)
        """,
        (name.lower(), str(path))
    )

    connection.commit()
    connection.close()


def find_folder(folder_name):
    connection = get_connection()
    cursor = connection.cursor()

    folder_name = folder_name.lower().strip()

    # First try exact match
    cursor.execute(
        """
        SELECT name, path
        FROM folders
        WHERE LOWER(name) = LOWER(?)
        LIMIT 1
        """,
        (folder_name,)
    )

    result = cursor.fetchone()

    if result:
        connection.close()
        return result

    # Second attempt:
    # Ignore spaces when comparing names
    normalized_name = folder_name.replace(" ", "")

    cursor.execute(
        """
        SELECT name, path
        FROM folders
        WHERE REPLACE(LOWER(name), ' ', '') = ?
        LIMIT 1
        """,
        (normalized_name,)
    )

    result = cursor.fetchone()

    connection.close()

    return result