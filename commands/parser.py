from actions.folder_actions import open_folder, close_folder
from actions.app_actions import open_application, close_application
from database.indexer import build_folder_index
from security.permissions import request_permission


def create_result(response, intent, success=True):
    """
    Create a standard command result.

    Every command processed by VoicePilot returns:
    - response: what VoicePilot should say
    - intent: what type of command was detected
    - success: whether the command succeeded
    """

    return {
        "response": response,
        "intent": intent,
        "success": success,
    }


def action_succeeded(response):
    """
    Temporarily determine whether an action succeeded
    based on the response returned by the action module.

    Later, action modules can return structured
    success values directly.
    """

    if not response:
        return False

    response_lower = str(response).lower()

    failure_phrases = [
        "not found",
        "could not",
        "couldn't",
        "unable",
        "failed",
        "not installed",
        "cannot",
        "can't",
        "no application",
        "no folder",
        "not recognized",
        "cancelled",
        "permission denied",
        "not currently open",
    ]

    for phrase in failure_phrases:
        if phrase in response_lower:
            return False

    return True


def process_command(command):
    command = command.lower().strip()

    # --------------------------------------------------
    # EXIT VOICEPILOT
    # --------------------------------------------------

    if command == "exit":
        return create_result(
            response="EXIT",
            intent="EXIT",
            success=True,
        )

    # --------------------------------------------------
    # REFRESH FOLDER INDEX
    # --------------------------------------------------

    elif command == "refresh folders":
        try:
            build_folder_index()

            return create_result(
                response="Folder index refreshed.",
                intent="REFRESH_FOLDERS",
                success=True,
            )

        except Exception as error:
            print(f"Folder indexing error: {error}")

            return create_result(
                response="I couldn't refresh the folder index.",
                intent="REFRESH_FOLDERS",
                success=False,
            )

    # --------------------------------------------------
    # TEST SECURITY CONFIRMATION
    # --------------------------------------------------

    elif command == "test confirmation":
        allowed = request_permission(
            "restart_computer",
            "This is a test confirmation. Do you want to continue?"
        )

        if allowed:
            return create_result(
                response="Confirmation accepted.",
                intent="TEST_CONFIRMATION",
                success=True,
            )

        return create_result(
            response="Action cancelled.",
            intent="TEST_CONFIRMATION",
            success=False,
        )

    # --------------------------------------------------
    # CLOSE FOLDER
    #
    # Important:
    # This must come BEFORE the generic "close "
    # application command.
    # --------------------------------------------------

    elif command.startswith("close folder "):
        folder_name = command.replace(
            "close folder ",
            "",
            1
        ).strip()

        response = close_folder(folder_name)

        return create_result(
            response=response,
            intent="CLOSE_FOLDER",
            success=action_succeeded(response),
        )

    # --------------------------------------------------
    # CLOSE APPLICATION
    # --------------------------------------------------

    elif command.startswith("close "):
        app_name = command.replace(
            "close ",
            "",
            1
        ).strip()

        response = close_application(app_name)

        return create_result(
            response=response,
            intent="CLOSE_APP",
            success=action_succeeded(response),
        )

    # --------------------------------------------------
    # OPEN FOLDER
    # --------------------------------------------------

    elif command.startswith("open folder "):
        folder_name = command.replace(
            "open folder ",
            "",
            1
        ).strip()

        response = open_folder(folder_name)

        return create_result(
            response=response,
            intent="OPEN_FOLDER",
            success=action_succeeded(response),
        )

    # --------------------------------------------------
    # OPEN APPLICATION OR COMMON FOLDER
    # --------------------------------------------------

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
            response = open_folder(target)

            return create_result(
                response=response,
                intent="OPEN_FOLDER",
                success=action_succeeded(response),
            )

        response = open_application(target)

        return create_result(
            response=response,
            intent="OPEN_APP",
            success=action_succeeded(response),
        )

    # --------------------------------------------------
    # UNKNOWN COMMAND
    # --------------------------------------------------

    return create_result(
        response="Command not recognized.",
        intent="UNKNOWN",
        success=False,
    )