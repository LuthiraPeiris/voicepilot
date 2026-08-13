from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from database.database import (
    add_file,
    add_folder,
    remove_file,
    remove_folder,
    update_file_path,
)
from database.indexer import load_search_locations


# --------------------------------------------------
# PATHS / FILES THAT VOICEPILOT MUST NOT WATCH
# --------------------------------------------------

IGNORED_FOLDER_NAMES = {
    "database",
    "venv",
    ".venv",
    "__pycache__",
    ".git",
    "node_modules",
}

IGNORED_FILE_NAMES = {
    "command.wav",
    "voicepilot.db",
    "voicepilot.db-journal",
    "voicepilot.db-wal",
    "voicepilot.db-shm",
}


def should_ignore(path):
    """
    Return True if a filesystem event belongs to
    VoicePilot's own internal/runtime files.
    """

    path = Path(path)

    # Ignore specific files
    if path.name.lower() in {
        name.lower()
        for name in IGNORED_FILE_NAMES
    }:
        return True

    # Ignore files inside internal folders
    for part in path.parts:
        if part.lower() in {
            name.lower()
            for name in IGNORED_FOLDER_NAMES
        }:
            return True

    # Ignore temporary SQLite files
    if path.name.lower().startswith(
        "voicepilot.db-"
    ):
        return True

    # Ignore temporary files
    if path.suffix.lower() in {
        ".tmp",
        ".temp",
    }:
        return True

    return False


class VoicePilotFileHandler(
    FileSystemEventHandler
):
    """
    Keep the VoicePilot SQLite index synchronized
    with filesystem changes.
    """

    def on_created(self, event):
        path = Path(event.src_path)

        if should_ignore(path):
            return

        try:
            if event.is_directory:
                add_folder(
                    path.name,
                    path,
                )

                print(
                    f"Indexed new folder: "
                    f"{path.name}"
                )

            else:
                add_file(
                    path.stem,
                    path.suffix,
                    path,
                )

                print(
                    f"Indexed new file: "
                    f"{path.name}"
                )

        except Exception as error:
            print(
                "Index watcher create error: "
                f"{error}"
            )


    def on_deleted(self, event):
        path = Path(event.src_path)

        if should_ignore(path):
            return

        try:
            if event.is_directory:
                remove_folder(path)

                print(
                    f"Removed folder from index: "
                    f"{path.name}"
                )

            else:
                remove_file(path)

                print(
                    f"Removed file from index: "
                    f"{path.name}"
                )

        except Exception as error:
            print(
                "Index watcher delete error: "
                f"{error}"
            )


    def on_moved(self, event):
        old_path = Path(event.src_path)
        new_path = Path(event.dest_path)

        if (
            should_ignore(old_path)
            or should_ignore(new_path)
        ):
            return

        try:
            if event.is_directory:
                remove_folder(
                    old_path
                )

                add_folder(
                    new_path.name,
                    new_path,
                )

                print(
                    f"Updated folder: "
                    f"{old_path.name} "
                    f"-> {new_path.name}"
                )

            else:
                update_file_path(
                    old_path,
                    new_path,
                )

                print(
                    f"Updated file: "
                    f"{old_path.name} "
                    f"-> {new_path.name}"
                )

        except Exception as error:
            print(
                "Index watcher move error: "
                f"{error}"
            )


def start_index_watcher():
    """
    Start filesystem monitoring in the background.
    """

    search_locations = (
        load_search_locations()
    )

    observer = Observer()

    event_handler = (
        VoicePilotFileHandler()
    )

    watched_locations = 0

    for location in search_locations:
        try:
            observer.schedule(
                event_handler,
                str(location),
                recursive=True,
            )

            watched_locations += 1

        except OSError as error:
            print(
                f"Could not watch "
                f"{location}: {error}"
            )

    if watched_locations == 0:
        print(
            "No locations available "
            "for file monitoring."
        )

        return None

    observer.start()

    print(
        "Automatic file indexing started."
    )

    return observer


def stop_index_watcher(observer):
    """
    Stop the background filesystem observer.
    """

    if observer is None:
        return

    observer.stop()
    observer.join()