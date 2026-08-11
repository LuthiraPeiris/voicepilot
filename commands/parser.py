from actions.folder_actions import open_folder
from actions.app_actions import open_application
from database.indexer import build_folder_index

def process_command(command):
    command = command.lower().strip()

    if command == "exit":
        return "EXIT"

    elif command == "refresh folders":

        build_folder_index()

        return "Folder index refreshed."

    elif command.startswith("open folder "):
        folder_name = command.replace("open folder ", "", 1).strip()
        return open_folder(folder_name)

    elif command.startswith("open "):
        target = command.replace("open ", "", 1).strip()

        # Common folders can still be opened naturally
        common_folders = [
            "desktop",
            "downloads",
            "documents",
            "pictures",
            "music",
            "videos",
        ]

        if target in common_folders:
            return open_folder(target)

        return open_application(target)

    return "Command not recognized."