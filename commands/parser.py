from actions.folder_actions import open_folder, close_folder
from actions.app_actions import open_application, close_application
from actions.system_actions import (
    volume_up,
    volume_down,
    mute_volume,
    lock_computer,
    restart_computer,
    shutdown_computer,
)
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
    # SYSTEM VOLUME - UP
    # --------------------------------------------------

    elif command in [
        "volume up",
        "increase volume",
        "turn volume up",
        "raise volume",
    ]:
        response = volume_up()

        return create_result(
            response=response,
            intent="VOLUME_UP",
            success=action_succeeded(response),
        )

    # --------------------------------------------------
    # SYSTEM VOLUME - DOWN
    # --------------------------------------------------

    elif command in [
        "volume down",
        "decrease volume",
        "turn volume down",
        "lower volume",
    ]:
        response = volume_down()

        return create_result(
            response=response,
            intent="VOLUME_DOWN",
            success=action_succeeded(response),
        )

    # --------------------------------------------------
    # MUTE AUDIO
    # --------------------------------------------------

    elif command in [
        "mute",
        "mute volume",
        "mute audio",
        "mute sound",
    ]:
        response = mute_volume()

        return create_result(
            response=response,
            intent="MUTE_VOLUME",
            success=action_succeeded(response),
        )

    # --------------------------------------------------
    # UNMUTE AUDIO
    #
    # For now, mute_volume() uses the Windows mute
    # toggle key, so this performs the same system
    # action as "mute".
    # --------------------------------------------------

    elif command in [
        "unmute",
        "unmute volume",
        "unmute audio",
        "unmute sound",
    ]:
        response = mute_volume()

        return create_result(
            response=response,
            intent="UNMUTE_VOLUME",
            success=action_succeeded(response),
        )

    # --------------------------------------------------
    # CLOSE FOLDER
    #
    # This must come before the generic "close "
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
    # LOCK COMPUTER
    # --------------------------------------------------

    elif command in [
        "lock computer",
        "lock pc",
        "lock my computer",
    ]:
        response = lock_computer()

        return create_result(
            response=response,
            intent="LOCK_COMPUTER",
            success=response == "LOCKED",
        )

    # --------------------------------------------------
    # RESTART COMPUTER
    # --------------------------------------------------

    elif command in [
        "restart computer",
        "restart pc",
        "restart my computer",
    ]:
        response = restart_computer()

        return create_result(
            response=response,
            intent="RESTART_COMPUTER",
            success=response == "RESTARTING",
        )

    # --------------------------------------------------
    # SHUTDOWN COMPUTER
    # --------------------------------------------------

    elif command in [
        "shutdown computer",
        "shut down computer",
        "shutdown pc",
        "shut down pc",
        "turn off computer",
    ]:
        response = shutdown_computer()

        return create_result(
            response=response,
            intent="SHUTDOWN_COMPUTER",
            success=response == "SHUTTING_DOWN",
        )

    # --------------------------------------------------
    # UNKNOWN COMMAND
    # --------------------------------------------------

    return create_result(
        response="Command not recognized.",
        intent="UNKNOWN",
        success=False,
    )