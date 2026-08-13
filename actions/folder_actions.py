import os
import subprocess
import winreg
from pathlib import Path

from security.permissions import request_permission
from database.database import find_folder


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
    """

    folder_name = folder_name.lower().strip()

    if folder_name not in WINDOWS_FOLDER_KEYS:
        return None

    path = get_windows_folder(folder_name)

    if not path:
        return f"{folder_name} folder was not found."

    try:
        os.startfile(path)

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


def find_folder_path(folder_name):
    """
    Resolve a folder name to its actual filesystem path.

    First checks Windows-known folders.
    Then searches the SQLite folder index.
    """

    folder_name = folder_name.lower().strip()

    common_path = get_windows_folder(folder_name)

    if common_path:
        return common_path

    return search_folder(folder_name)


def open_folder(folder_name):
    """
    Open a folder.

    First checks common Windows folders.
    If it is not a common folder, searches
    the SQLite folder index.
    """

    if not request_permission("open_folder"):
        return "Permission denied."

    folder_name = folder_name.lower().strip()

    # Check Windows-known folders first
    common_result = open_common_folder(folder_name)

    if common_result:
        return common_result

    # Search SQLite folder index
    match = search_folder(folder_name)

    if match:
        try:
            os.startfile(match)

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

        return f"The {folder_name} folder is not currently open."

    except Exception as error:
        print(f"Folder closing error: {error}")

        return f"I couldn't close the {folder_name} folder."