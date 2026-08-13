from security.confirmation import (
    ask_for_confirmation,
)


SAFE_ACTIONS = {
    "open_application",
    "open_folder",
    "open_website",
    "create_folder",
    "create_file",
    "open_file",
}


CONFIRM_ACTIONS = {
    "close_application",
    "close_folder",
    "restart_computer",
    "shutdown_computer",
    "rename_file",
    "rename_folder",
    "delete_file",
    "delete_folder",
}


BLOCKED_ACTIONS = {
    "delete_system_file",
    "disable_security",
    "run_admin_command",
}


def get_permission_level(
    action_name,
):
    """
    Return the security level for
    an action.
    """

    if not action_name:
        return "UNKNOWN"

    action_name = (
        action_name
        .lower()
        .strip()
    )

    if action_name in SAFE_ACTIONS:
        return "SAFE"

    if action_name in CONFIRM_ACTIONS:
        return "CONFIRM"

    if action_name in BLOCKED_ACTIONS:
        return "BLOCKED"

    return "UNKNOWN"


def request_permission(
    action_name,
    confirmation_message=None,
):
    """
    Check whether an action is allowed.

    SAFE:
        Immediately allowed.

    CONFIRM:
        Requires spoken confirmation.

    BLOCKED:
        Always rejected.

    UNKNOWN:
        Rejected by default.
    """

    level = get_permission_level(
        action_name
    )

    print(
        f"Permission request: "
        f"{action_name} -> {level}"
    )

    # --------------------------------------
    # SAFE
    # --------------------------------------

    if level == "SAFE":
        return True

    # --------------------------------------
    # CONFIRMATION REQUIRED
    # --------------------------------------

    if level == "CONFIRM":
        if not confirmation_message:
            confirmation_message = (
                "This action requires "
                "confirmation. "
                "Do you want to continue?"
            )

        return ask_for_confirmation(
            confirmation_message
        )

    # --------------------------------------
    # BLOCKED
    # --------------------------------------

    if level == "BLOCKED":
        print(
            "Permission denied. "
            "This action is blocked."
        )

        return False

    # --------------------------------------
    # UNKNOWN ACTION
    # --------------------------------------

    print(
        "Permission denied. "
        "Unknown actions are blocked "
        "by default."
    )

    return False