import os
import subprocess
from pathlib import Path

from security.permissions import request_permission
from database.database import find_folder


COMMON_FOLDERS = {
    "desktop": Path.home() / "Desktop",
    "downloads": Path.home() / "Downloads",
    "documents": Path.home() / "Documents",
    "pictures": Path.home() / "Pictures",
    "music": Path.home() / "Music",
    "videos": Path.home() / "Videos",
}


def get_common_folder(folder_name):
    """
    Return the path of a common Windows folder.
    """

    folder_name = folder_name.lower().strip()

    if folder_name not in COMMON_FOLDERS:
        return None

    path = COMMON_FOLDERS[folder_name]

    if path.exists():
        return path

    return None


def open_common_folder(folder_name):
    """
    Open common Windows user folders such as
    Desktop, Downloads, Documents, Pictures, Music, and Videos.
    """

    folder_name = folder_name.lower().strip()

    path = get_common_folder(folder_name)

    if path:
        os.startfile(path)
        return f"Opening {folder_name}."

    if folder_name in COMMON_FOLDERS:
        return f"{folder_name} folder was not found."

    return None


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

    # Make sure the folder still exists on the computer
    if folder_path.exists() and folder_path.is_dir():
        return folder_path

    return None


def find_folder_path(folder_name):
    """
    Resolve a folder name to its actual filesystem path.

    First checks common Windows folders.
    Then searches the SQLite folder index.
    """

    folder_name = folder_name.lower().strip()

    common_path = get_common_folder(folder_name)

    if common_path:
        return common_path

    return search_folder(folder_name)


def open_folder(folder_name):
    """
    Open a folder.

    First checks common Windows folders.
    If it is not a common folder, search the SQLite folder index.
    """

    if not request_permission("open_folder"):
        return "Permission denied."

    folder_name = folder_name.lower().strip()

    # Check common Windows folders first
    common_result = open_common_folder(folder_name)

    if common_result:
        return common_result

    # Search SQLite folder index
    match = search_folder(folder_name)

    if match:
        try:
            os.startfile(match)
            return f"Opening {match.name}."

        except OSError:
            return f"I found {match}, but I couldn't open it."

    return f"I couldn't find a folder called {folder_name}."


def close_folder(folder_name):
    """
    Close a File Explorer window that is currently displaying
    the requested folder.
    """

    if not request_permission("close_folder"):
        return "Permission denied."

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