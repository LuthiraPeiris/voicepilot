import os
import subprocess
import winreg
from pathlib import Path

from security.permissions import request_permission
from database.database import find_folder
from context.folder_context import (
    set_current_folder,
    get_current_folder,
)


SHELL_FOLDER_REGISTRY_PATH = (
    r"Software\Microsoft\Windows\CurrentVersion"
    r"\Explorer\User Shell Folders"
)


WINDOWS_FOLDER_KEYS = {
    "desktop": "Desktop",
    "documents": "Personal",
    "pictures": "My Pictures",
    "music": "My Music",
    "videos": "My Video",
    "downloads": "{374DE290-123F-4565-9164-39C4925E467B}",
}


def get_windows_folder(folder_name):
    """
    Get the actual Windows path for a common user folder.
    Supports redirected folders such as OneDrive.
    """

    folder_name = folder_name.lower().strip()

    registry_value = WINDOWS_FOLDER_KEYS.get(folder_name)

    if not registry_value:
        return None

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            SHELL_FOLDER_REGISTRY_PATH,
        ) as key:
            folder_path, _ = winreg.QueryValueEx(
                key,
                registry_value,
            )

        folder_path = os.path.expandvars(folder_path)

        path = Path(folder_path)

        if path.exists() and path.is_dir():
            return path

        return None

    except (FileNotFoundError, OSError):
        return None


def open_common_folder(folder_name):
    """
    Open common Windows user folders such as
    Desktop, Downloads, Documents, Pictures, Music, and Videos.

    When successfully opened, the folder becomes
    VoicePilot's current working folder.
    """

    folder_name = folder_name.lower().strip()

    if folder_name not in WINDOWS_FOLDER_KEYS:
        return None

    path = get_windows_folder(folder_name)

    if not path:
        return f"{folder_name} folder was not found."

    try:
        os.startfile(path)

        # Remember this folder as the current context
        set_current_folder(path)

        return f"Opening {folder_name}."

    except OSError as error:
        print(f"Open common folder error: {error}")

        return f"I couldn't open the {folder_name} folder."


def search_folder(folder_name):
    """
    Search for a folder using the SQLite folder index.
    """

    folder_name = folder_name.lower().strip()

    result = find_folder(folder_name)

    if not result:
        return None

    name, path = result

    folder_path = Path(path)

    if folder_path.exists() and folder_path.is_dir():
        return folder_path

    return None


def search_folder_in_current_folder(folder_name):
    """
    Search for a child folder inside the current
    VoicePilot working folder.

    Example:

    Current folder:
    Downloads

    Command:
    open folder projects

    VoicePilot first checks:
    Downloads/projects
    """

    current_folder = get_current_folder()

    if not current_folder:
        return None

    folder_name = folder_name.strip()

    try:
        # Exact child folder path first
        candidate = current_folder / folder_name

        if candidate.exists() and candidate.is_dir():
            return candidate

        # Case-insensitive child folder search
        for item in current_folder.iterdir():
            if (
                item.is_dir()
                and item.name.lower() == folder_name.lower()
            ):
                return item

    except (PermissionError, OSError):
        return None

    return None


def find_folder_path(folder_name):
    """
    Resolve a folder name to its actual filesystem path.

    Search order:
    1. Current working folder
    2. Windows-known folders
    3. Global SQLite folder index
    """

    folder_name = folder_name.lower().strip()

    # Check inside current working folder first
    current_match = search_folder_in_current_folder(
        folder_name
    )

    if current_match:
        return current_match

    # Check common Windows folders
    common_path = get_windows_folder(folder_name)

    if common_path:
        return common_path

    # Fall back to global folder index
    return search_folder(folder_name)


def open_folder(folder_name):
    """
    Open a folder and make it VoicePilot's
    current working folder.

    Search order:
    1. Windows-known folder
    2. Folder inside current working folder
    3. Global SQLite folder index
    """

    if not request_permission("open_folder"):
        return "Permission denied."

    folder_name = folder_name.lower().strip()

    # --------------------------------------------------
    # COMMON WINDOWS FOLDERS
    # --------------------------------------------------

    common_result = open_common_folder(folder_name)

    if common_result:
        return common_result

    # --------------------------------------------------
    # CURRENT FOLDER
    # --------------------------------------------------

    current_match = search_folder_in_current_folder(
        folder_name
    )

    if current_match:
        try:
            os.startfile(current_match)

            set_current_folder(current_match)

            return f"Opening {current_match.name}."

        except OSError as error:
            print(f"Open folder error: {error}")

            return (
                f"I found {current_match}, "
                "but I couldn't open it."
            )

    # --------------------------------------------------
    # GLOBAL FOLDER INDEX
    # --------------------------------------------------

    match = search_folder(folder_name)

    if match:
        try:
            os.startfile(match)

            set_current_folder(match)

            return f"Opening {match.name}."

        except OSError as error:
            print(f"Open folder error: {error}")

            return f"I found {match}, but I couldn't open it."

    return f"I couldn't find a folder called {folder_name}."


def close_folder(folder_name):
    """
    Close a File Explorer window that is currently
    displaying the requested folder.
    """

    if not request_permission(
        "close_folder",
        f"Do you want me to close the {folder_name} folder?"
    ):
        return "Action cancelled."

    folder_name = folder_name.lower().strip()

    folder_path = find_folder_path(folder_name)

    if not folder_path:
        return f"I couldn't find a folder called {folder_name}."

    try:
        resolved_path = str(folder_path.resolve())

        powershell_script = r"""
$targetPath = [System.IO.Path]::GetFullPath($env:VOICEPILOT_FOLDER_PATH)

$shell = New-Object -ComObject Shell.Application
$closed = $false

foreach ($window in $shell.Windows()) {
    try {
        if (-not $window.Document) {
            continue
        }

        $windowPath = $window.Document.Folder.Self.Path

        if (-not $windowPath) {
            continue
        }

        $windowFullPath = [System.IO.Path]::GetFullPath($windowPath)

        if ($windowFullPath.TrimEnd('\') -ieq $targetPath.TrimEnd('\')) {
            $window.Quit()
            $closed = $true
        }
    }
    catch {
        continue
    }
}

if ($closed) {
    Write-Output "CLOSED"
}
else {
    Write-Output "NOT_FOUND"
}
"""

        environment = os.environ.copy()
        environment["VOICEPILOT_FOLDER_PATH"] = resolved_path

        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                powershell_script,
            ],
            capture_output=True,
            text=True,
            env=environment,
        )

        output = result.stdout.strip()

        if "CLOSED" in output:
            return f"Closing folder {folder_name}."

        return (
            f"The {folder_name} folder "
            "is not currently open."
        )

    except Exception as error:
        print(f"Folder closing error: {error}")

        return f"I couldn't close the {folder_name} folder."