import sqlite3
from pathlib import Path


DATABASE_PATH = Path("database") / "voicepilot.db"


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    return connection


def create_tables():
    connection = get_connection()
    cursor = connection.cursor()

    # --------------------------------------------------
    # FOLDERS
    # --------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS folders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            path TEXT NOT NULL UNIQUE
        )
        """
    )

    # --------------------------------------------------
    # FILES
    # --------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            extension TEXT,
            path TEXT NOT NULL UNIQUE
        )
        """
    )

    # --------------------------------------------------
    # COMMAND HISTORY
    # --------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS command_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            command TEXT NOT NULL,
            intent TEXT,
            success INTEGER NOT NULL DEFAULT 1,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()
    connection.close()


# ==================================================
# FOLDER DATABASE FUNCTIONS
# ==================================================


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
        INSERT OR IGNORE INTO folders (
            name,
            path
        )
        VALUES (?, ?)
        """,
        (
            name.lower(),
            str(path),
        ),
    )

    connection.commit()
    connection.close()


def find_folder(folder_name):
    connection = get_connection()
    cursor = connection.cursor()

    folder_name = folder_name.lower().strip()

    # Exact match
    cursor.execute(
        """
        SELECT name, path
        FROM folders
        WHERE LOWER(name) = LOWER(?)
        LIMIT 1
        """,
        (folder_name,),
    )

    result = cursor.fetchone()

    if result:
        connection.close()
        return result

    # Ignore spaces
    normalized_name = folder_name.replace(" ", "")

    cursor.execute(
        """
        SELECT name, path
        FROM folders
        WHERE REPLACE(LOWER(name), ' ', '') = ?
        LIMIT 1
        """,
        (normalized_name,),
    )

    result = cursor.fetchone()

    connection.close()

    return result


# ==================================================
# FILE DATABASE FUNCTIONS
# ==================================================


def clear_files():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM files")

    connection.commit()
    connection.close()


def add_file(name, extension, path):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT OR IGNORE INTO files (
            name,
            extension,
            path
        )
        VALUES (?, ?, ?)
        """,
        (
            name.lower(),
            extension.lower(),
            str(path),
        ),
    )

    connection.commit()
    connection.close()


def find_file(file_name):
    """
    Search for a file by:

    1. Exact filename including extension
    2. Exact filename without extension
    3. Filename ignoring spaces
    4. Partial filename match
    """

    connection = get_connection()
    cursor = connection.cursor()

    file_name = file_name.lower().strip()

    # --------------------------------------------------
    # 1. Exact filename
    # Example: resume.pdf
    # --------------------------------------------------

    cursor.execute(
        """
        SELECT name, extension, path
        FROM files
        WHERE LOWER(name || extension) = LOWER(?)
        LIMIT 1
        """,
        (file_name,),
    )

    result = cursor.fetchone()

    if result:
        connection.close()
        return result

    # --------------------------------------------------
    # 2. Exact name without extension
    # Example: resume
    # --------------------------------------------------

    cursor.execute(
        """
        SELECT name, extension, path
        FROM files
        WHERE LOWER(name) = LOWER(?)
        LIMIT 1
        """,
        (file_name,),
    )

    result = cursor.fetchone()

    if result:
        connection.close()
        return result

    # --------------------------------------------------
    # 3. Ignore spaces
    # Example:
    # "project report"
    # can match "projectreport"
    # --------------------------------------------------

    normalized_name = file_name.replace(" ", "")

    cursor.execute(
        """
        SELECT name, extension, path
        FROM files
        WHERE REPLACE(LOWER(name), ' ', '') = ?
        LIMIT 1
        """,
        (normalized_name,),
    )

    result = cursor.fetchone()

    if result:
        connection.close()
        return result

    # --------------------------------------------------
    # 4. Partial name
    # --------------------------------------------------

    cursor.execute(
        """
        SELECT name, extension, path
        FROM files
        WHERE LOWER(name) LIKE ?
        ORDER BY LENGTH(name) ASC
        LIMIT 1
        """,
        (f"%{file_name}%",),
    )

    result = cursor.fetchone()

    connection.close()

    return result