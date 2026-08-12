from database.database import get_connection


MAX_HISTORY_RECORDS = 5000


def save_command(command, intent=None, success=True):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO command_history (
            command,
            intent,
            success
        )
        VALUES (?, ?, ?)
        """,
        (
            command,
            intent,
            1 if success else 0
        )
    )

    connection.commit()
    connection.close()

    cleanup_history()


def cleanup_history():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM command_history
        WHERE id NOT IN (
            SELECT id
            FROM command_history
            ORDER BY id DESC
            LIMIT ?
        )
        """,
        (MAX_HISTORY_RECORDS,)
    )

    connection.commit()
    connection.close()


def get_recent_commands(limit=20):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            id,
            command,
            intent,
            success,
            timestamp
        FROM command_history
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,)
    )

    rows = cursor.fetchall()

    connection.close()

    return rows