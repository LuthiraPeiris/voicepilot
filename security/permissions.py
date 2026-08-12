from security.confirmation import ask_for_confirmation


SAFE_ACTIONS = {
    "open_application",
    "open_folder",
    "open_website",
    "create_folder",
    "open_file",
}


CONFIRM_ACTIONS = {
    "close_application",
    "close_folder",
    "restart_computer",
    "shutdown_computer",
    "move_file",
    "rename_file",
    "rename_folder",
}


BLOCKED_ACTIONS = {
    "delete_system_file",
    "disable_security",
    "run_admin_command",
}


def get_permission_level(action_name):
    if action_name in SAFE_ACTIONS:
        return "SAFE"

    if action_name in CONFIRM_ACTIONS:
        return "CONFIRM"

    if action_name in BLOCKED_ACTIONS:
        return "BLOCKED"

    return "UNKNOWN"


def request_permission(action_name, confirmation_message=None):
    level = get_permission_level(action_name)

    if level == "SAFE":
        return True

    if level == "CONFIRM":
        if not confirmation_message:
            confirmation_message = (
                "This action requires confirmation. "
                "Do you want to continue?"
            )

        return ask_for_confirmation(
            confirmation_message
        )

    if level == "BLOCKED":
        return False

    return False