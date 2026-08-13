from actions.folder_actions import (
    open_folder,
    close_folder,
    navigate_to_parent_folder,
)

from actions.app_actions import (
    open_application,
    close_application,
)

from actions.file_actions import (
    create_folder,
    create_file,
    delete_file,
    delete_folder,
    rename_file,
    rename_folder,
    open_file,
    has_pending_file_selection,
    select_pending_file,
)

from actions.system_actions import (
    volume_up,
    volume_down,
    mute_volume,
    lock_computer,
    restart_computer,
    shutdown_computer,
)

from context.folder_context import (
    get_current_folder,
)

from context.rename_context import (
    set_pending_rename,
    get_pending_rename,
    has_pending_rename,
    clear_pending_rename,
)

from database.indexer import build_folder_index
from security.permissions import request_permission


def create_result(
    response,
    intent,
    success=True,
):
    return {
        "response": response,
        "intent": intent,
        "success": success,
    }


def action_succeeded(response):
    if not response:
        return False

    response_lower = (
        str(response).lower()
    )

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
        "already exists",
        "cannot be empty",
        "don't recognize",
        "couldn't find",
    ]

    for phrase in failure_phrases:
        if phrase in response_lower:
            return False

    return True


def process_command(command):
    command = command.lower().strip()

    # --------------------------------------------------
    # EXIT
    # --------------------------------------------------

    if command == "exit":
        return create_result(
            response="EXIT",
            intent="EXIT",
            success=True,
        )

    # --------------------------------------------------
    # REFRESH INDEX
    # --------------------------------------------------

    elif command in [
        "refresh folders",
        "refresh files",
        "refresh index",
    ]:
        try:
            build_folder_index()

            return create_result(
                response=(
                    "File and folder index refreshed."
                ),
                intent="REFRESH_INDEX",
                success=True,
            )

        except Exception as error:
            print(
                f"Indexing error: {error}"
            )

            return create_result(
                response=(
                    "I couldn't refresh the "
                    "file and folder index."
                ),
                intent="REFRESH_INDEX",
                success=False,
            )

    # --------------------------------------------------
    # TEST CONFIRMATION
    # --------------------------------------------------

    elif command == "test confirmation":
        allowed = request_permission(
            "restart_computer",
            (
                "This is a test confirmation. "
                "Do you want to continue?"
            ),
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
    # VOLUME UP
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
            success=action_succeeded(
                response
            ),
        )

    # --------------------------------------------------
    # VOLUME DOWN
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
            success=action_succeeded(
                response
            ),
        )

    # --------------------------------------------------
    # MUTE
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
            success=action_succeeded(
                response
            ),
        )

    # --------------------------------------------------
    # UNMUTE
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
            success=action_succeeded(
                response
            ),
        )

    # --------------------------------------------------
    # LOCK
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
    # RESTART
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
            success=(
                response == "RESTARTING"
            ),
        )

    # --------------------------------------------------
    # SHUTDOWN
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
            success=(
                response
                == "SHUTTING_DOWN"
            ),
        )

    # --------------------------------------------------
    # GO BACK
    #
    # Reuses the same Explorer window/tab.
    # --------------------------------------------------

    elif command in [
        "go back",
        "go up",
        "back",
        "go to parent folder",
        "parent folder",
        "one folder back",
    ]:
        result = (
            navigate_to_parent_folder()
        )

        return create_result(
            response=result["response"],
            intent="GO_BACK",
            success=result["success"],
        )

    # --------------------------------------------------
    # WHERE AM I
    # --------------------------------------------------

    elif command in [
        "where am i",
        "current folder",
        "what folder am i in",
        "which folder am i in",
    ]:
        current_folder = (
            get_current_folder()
        )

        if not current_folder:
            return create_result(
                response=(
                    "There is no current folder."
                ),
                intent="CURRENT_FOLDER",
                success=False,
            )

        folder_name = (
            current_folder.name
        )

        if not folder_name:
            folder_name = str(
                current_folder
            )

        return create_result(
            response=(
                f"You are currently in "
                f"{folder_name}."
            ),
            intent="CURRENT_FOLDER",
            success=True,
        )

    # --------------------------------------------------
    # CREATE FILE
    # --------------------------------------------------

    elif command.startswith(
        "create file "
    ):
        file_name = command.replace(
            "create file ",
            "",
            1,
        ).strip()

        response = create_file(
            file_name
        )

        return create_result(
            response=response,
            intent="CREATE_FILE",
            success=action_succeeded(
                response
            ),
        )

    # --------------------------------------------------
    # CREATE FOLDER
    # --------------------------------------------------

    elif command.startswith(
        "create folder "
    ):
        folder_name = command.replace(
            "create folder ",
            "",
            1,
        ).strip()

        response = create_folder(
            folder_name
        )

        return create_result(
            response=response,
            intent="CREATE_FOLDER",
            success=action_succeeded(
                response
            ),
        )

    # --------------------------------------------------
    # RENAME FILE - ONE COMMAND
    # --------------------------------------------------

    elif (
        command.startswith(
            "rename file "
        )
        and " to " in command
    ):
        content = command.replace(
            "rename file ",
            "",
            1,
        )

        old_name, new_name = (
            content.split(
                " to ",
                1,
            )
        )

        clear_pending_rename()

        response = rename_file(
            old_name.strip(),
            new_name.strip(),
        )

        return create_result(
            response=response,
            intent="RENAME_FILE",
            success=action_succeeded(
                response
            ),
        )

    # --------------------------------------------------
    # RENAME FOLDER - ONE COMMAND
    # --------------------------------------------------

    elif (
        command.startswith(
            "rename folder "
        )
        and " to " in command
    ):
        content = command.replace(
            "rename folder ",
            "",
            1,
        )

        old_name, new_name = (
            content.split(
                " to ",
                1,
            )
        )

        clear_pending_rename()

        response = rename_folder(
            old_name.strip(),
            new_name.strip(),
        )

        return create_result(
            response=response,
            intent="RENAME_FOLDER",
            success=action_succeeded(
                response
            ),
        )

    # --------------------------------------------------
    # START TWO-STEP FILE RENAME
    # --------------------------------------------------

    elif command.startswith(
        "rename file "
    ):
        old_name = command.replace(
            "rename file ",
            "",
            1,
        ).strip()

        if not old_name:
            return create_result(
                response=(
                    "Tell me which file "
                    "you want to rename."
                ),
                intent="RENAME_FILE_START",
                success=False,
            )

        set_pending_rename(
            "file",
            old_name,
        )

        return create_result(
            response=(
                "What should I rename it to?"
            ),
            intent="RENAME_FILE_START",
            success=True,
        )

    # --------------------------------------------------
    # START TWO-STEP FOLDER RENAME
    # --------------------------------------------------

    elif command.startswith(
        "rename folder "
    ):
        old_name = command.replace(
            "rename folder ",
            "",
            1,
        ).strip()

        if not old_name:
            return create_result(
                response=(
                    "Tell me which folder "
                    "you want to rename."
                ),
                intent="RENAME_FOLDER_START",
                success=False,
            )

        set_pending_rename(
            "folder",
            old_name,
        )

        return create_result(
            response=(
                "What should I rename it to?"
            ),
            intent="RENAME_FOLDER_START",
            success=True,
        )

    # --------------------------------------------------
    # PENDING RENAME RESPONSE
    # --------------------------------------------------

    elif has_pending_rename():
        pending = (
            get_pending_rename()
        )

        if command in [
            "cancel",
            "never mind",
            "nevermind",
            "stop",
        ]:
            clear_pending_rename()

            return create_result(
                response="Rename cancelled.",
                intent="RENAME_CANCEL",
                success=False,
            )

        item_type = (
            pending["type"]
        )

        old_name = (
            pending["old_name"]
        )

        new_name = (
            command.strip()
        )

        clear_pending_rename()

        if item_type == "file":
            response = rename_file(
                old_name,
                new_name,
            )

            return create_result(
                response=response,
                intent="RENAME_FILE",
                success=action_succeeded(
                    response
                ),
            )

        if item_type == "folder":
            response = rename_folder(
                old_name,
                new_name,
            )

            return create_result(
                response=response,
                intent="RENAME_FOLDER",
                success=action_succeeded(
                    response
                ),
            )

        return create_result(
            response=(
                "I couldn't complete "
                "the rename."
            ),
            intent="RENAME",
            success=False,
        )

    # --------------------------------------------------
    # DELETE FILE
    # --------------------------------------------------

    elif command.startswith(
        "delete file "
    ):
        file_name = command.replace(
            "delete file ",
            "",
            1,
        ).strip()

        response = delete_file(
            file_name
        )

        return create_result(
            response=response,
            intent="DELETE_FILE",
            success=action_succeeded(
                response
            ),
        )

    # --------------------------------------------------
    # DELETE FOLDER
    # --------------------------------------------------

    elif command.startswith(
        "delete folder "
    ):
        folder_name = command.replace(
            "delete folder ",
            "",
            1,
        ).strip()

        response = delete_folder(
            folder_name
        )

        return create_result(
            response=response,
            intent="DELETE_FOLDER",
            success=action_succeeded(
                response
            ),
        )

    # --------------------------------------------------
    # OPEN FILE
    # --------------------------------------------------

    elif (
        command.startswith(
            "open file "
        )
        or command.startswith(
            "open the file "
        )
    ):
        if command.startswith(
            "open the file "
        ):
            file_name = command.replace(
                "open the file ",
                "",
                1,
            ).strip()

        else:
            file_name = command.replace(
                "open file ",
                "",
                1,
            ).strip()

        result = open_file(
            file_name
        )

        return create_result(
            response=result["response"],
            intent="OPEN_FILE",
            success=result["success"],
        )

    # --------------------------------------------------
    # CLOSE FOLDER
    # --------------------------------------------------

    elif command.startswith(
        "close folder "
    ):
        folder_name = command.replace(
            "close folder ",
            "",
            1,
        ).strip()

        response = close_folder(
            folder_name
        )

        return create_result(
            response=response,
            intent="CLOSE_FOLDER",
            success=action_succeeded(
                response
            ),
        )

    # --------------------------------------------------
    # CLOSE APPLICATION
    # --------------------------------------------------

    elif command.startswith(
        "close "
    ):
        app_name = command.replace(
            "close ",
            "",
            1,
        ).strip()

        response = close_application(
            app_name
        )

        return create_result(
            response=response,
            intent="CLOSE_APP",
            success=action_succeeded(
                response
            ),
        )

    # --------------------------------------------------
    # OPEN FOLDER
    # --------------------------------------------------

    elif command.startswith(
        "open folder "
    ):
        folder_name = command.replace(
            "open folder ",
            "",
            1,
        ).strip()

        response = open_folder(
            folder_name
        )

        return create_result(
            response=response,
            intent="OPEN_FOLDER",
            success=action_succeeded(
                response
            ),
        )

    # --------------------------------------------------
    # OPEN APPLICATION OR COMMON FOLDER
    # --------------------------------------------------

    elif command.startswith(
        "open "
    ):
        target = command.replace(
            "open ",
            "",
            1,
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
            response = open_folder(
                target
            )

            return create_result(
                response=response,
                intent="OPEN_FOLDER",
                success=action_succeeded(
                    response
                ),
            )

        response = open_application(
            target
        )

        return create_result(
            response=response,
            intent="OPEN_APP",
            success=action_succeeded(
                response
            ),
        )

    # --------------------------------------------------
    # PENDING FILE SELECTION
    # --------------------------------------------------

    elif has_pending_file_selection():
        result = select_pending_file(
            command
        )

        return create_result(
            response=result["response"],
            intent="OPEN_FILE_SELECTION",
            success=result["success"],
        )

    # --------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------

    return create_result(
        response="Command not recognized.",
        intent="UNKNOWN",
        success=False,
    )