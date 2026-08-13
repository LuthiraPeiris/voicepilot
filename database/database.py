import sqlite3
from pathlib import Path


DATABASE_PATH = Path("database") / "voicepilot.db"


def get_connection():
    return sqlite3.connect(DATABASE_PATH)


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
# FOLDERS
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
        INSERT OR IGNORE INTO folders (name, path)
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
# FILES
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


def find_files(file_name, limit=5):
    """
    Return multiple matching files.

    Search order:
    1. Exact full filename
    2. Exact filename without extension
    3. Name ignoring spaces
    4. Partial filename
    """

    connection = get_connection()
    cursor = connection.cursor()

    file_name = file_name.lower().strip()

    # --------------------------------------------------
    # EXACT FULL NAME
    # resume.pdf
    # --------------------------------------------------

    cursor.execute(
        """
        SELECT name, extension, path
        FROM files
        WHERE LOWER(name || extension) = LOWER(?)
        LIMIT ?
        """,
        (
            file_name,
            limit,
        ),
    )

    results = cursor.fetchall()

    if results:
        connection.close()
        return results

    # --------------------------------------------------
    # EXACT NAME WITHOUT EXTENSION
    # resume
    # --------------------------------------------------

    cursor.execute(
        """
        SELECT name, extension, path
        FROM files
        WHERE LOWER(name) = LOWER(?)
        LIMIT ?
        """,
        (
            file_name,
            limit,
        ),
    )

    results = cursor.fetchall()

    if results:
        connection.close()
        return results

    # --------------------------------------------------
    # IGNORE SPACES
    # --------------------------------------------------

    normalized_name = file_name.replace(" ", "")

    cursor.execute(
        """
        SELECT name, extension, path
        FROM files
        WHERE REPLACE(LOWER(name), ' ', '') = ?
        LIMIT ?
        """,
        (
            normalized_name,
            limit,
        ),
    )

    results = cursor.fetchall()

    if results:
        connection.close()
        return results

    # --------------------------------------------------
    # PARTIAL MATCH
    # --------------------------------------------------

    cursor.execute(
        """
        SELECT name, extension, path
        FROM files
        WHERE LOWER(name) LIKE ?
        ORDER BY LENGTH(name) ASC
        LIMIT ?
        """,
        (
            f"%{file_name}%",
            limit,
        ),
    )

    results = cursor.fetchall()

    connection.close()

    return results


def find_file(file_name):
    """
    Compatibility helper.

    Returns the first matching file.
    """

    results = find_files(
        file_name,
        limit=1,
    )

    if not results:
        return None

    return results[0]


def remove_file(path):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM files
        WHERE path = ?
        """,
        (str(path),),
    )

    connection.commit()
    connection.close()


def remove_folder(path):
    connection = get_connection()
    cursor = connection.cursor()

    path = str(path)

    cursor.execute(
        """
        DELETE FROM folders
        WHERE path = ?
        OR path LIKE ?
        """,
        (
            path,
            f"{path}\\%",
        ),
    )

    cursor.execute(
        """
        DELETE FROM files
        WHERE path LIKE ?
        """,
        (
            f"{path}\\%",
        ),
    )

    connection.commit()
    connection.close()


def update_file_path(
    old_path,
    new_path,
):
    """
    Update an indexed file after it has been
    renamed or moved.
    """

    old_path = Path(old_path)
    new_path = Path(new_path)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM files
        WHERE path = ?
        """,
        (str(old_path),),
    )

    connection.commit()
    connection.close()

    if (
        new_path.exists()
        and new_path.is_file()
    ):
        add_file(
            new_path.stem,
            new_path.suffix,
            new_path,
        )