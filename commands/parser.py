from actions.folder_actions import open_folder
from actions.app_actions import open_application, close_application
from database.indexer import build_folder_index
from security.permissions import request_permission


def process_command(command):
    command = command.lower().strip()

    if command == "exit":
        return "EXIT"

    elif command == "refresh folders":
        build_folder_index()
        return "Folder index refreshed."

    elif command == "test confirmation":
        allowed = request_permission(
            "restart_computer",
            "This is a test confirmation. Do you want to continue?"
        )

        if allowed:
            return "Confirmation accepted."

        return "Action cancelled."

    elif command.startswith("close "):
        app_name = command.replace(
            "close ",
            "",
            1
        ).strip()

        return close_application(app_name)

    elif command.startswith("open folder "):
        folder_name = command.replace(
            "open folder ",
            "",
            1
        ).strip()

        return open_folder(folder_name)

    elif command.startswith("open "):
        target = command.replace(
            "open ",
            "",
            1
        ).strip()

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