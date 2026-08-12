import json
import shutil
import subprocess
from difflib import SequenceMatcher

from security.permissions import request_permission


ALIASES = {
    "vscode": "visual studio code",
    "vs code": "visual studio code",
    "code": "visual studio code",

    "edge": "microsoft edge",
    "browser": "google chrome",

    "chrome": "google chrome",

    "word": "microsoft word",
    "excel": "microsoft excel",
    "powerpoint": "microsoft powerpoint",

    "terminal": "windows terminal",
    "cmd": "command prompt",
}


PROCESS_ALIASES = {
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",

    "vscode": "Code.exe",
    "vs code": "Code.exe",
    "visual studio code": "Code.exe",
    "code": "Code.exe",

    "spotify": "Spotify.exe",

    "notepad": "notepad.exe",

    "calculator": "CalculatorApp.exe",

    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",

    "word": "WINWORD.EXE",
    "microsoft word": "WINWORD.EXE",

    "excel": "EXCEL.EXE",
    "microsoft excel": "EXCEL.EXE",

    "powerpoint": "POWERPNT.EXE",
    "microsoft powerpoint": "POWERPNT.EXE",

    "terminal": "WindowsTerminal.exe",
    "windows terminal": "WindowsTerminal.exe",
}


def get_installed_apps():
    powershell_command = """
    Get-StartApps |
    Select-Object Name, AppID |
    ConvertTo-Json -Compress
    """

    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                powershell_command,
            ],
            capture_output=True,
            text=True,
            check=True,
        )

        output = result.stdout.strip()

        if not output:
            return {}

        apps = json.loads(output)

        if isinstance(apps, dict):
            apps = [apps]

        installed_apps = {}

        for app in apps:
            name = app.get("Name")
            app_id = app.get("AppID")

            if name and app_id:
                installed_apps[name.lower()] = app_id

        return installed_apps

    except (
        subprocess.CalledProcessError,
        json.JSONDecodeError,
    ):
        return {}


def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def find_application(app_name):
    app_name = app_name.lower().strip()

    # 1. Resolve aliases
    if app_name in ALIASES:
        app_name = ALIASES[app_name]

    installed_apps = get_installed_apps()

    # 2. Exact match
    if app_name in installed_apps:
        return app_name, installed_apps[app_name]

    # 3. Partial match
    for installed_name, app_id in installed_apps.items():
        if app_name in installed_name:
            return installed_name, app_id

    # 4. Fuzzy matching
    best_match = None
    best_score = 0

    for installed_name, app_id in installed_apps.items():
        score = similarity(app_name, installed_name)

        if score > best_score:
            best_score = score
            best_match = (
                installed_name,
                app_id,
            )

    # Avoid opening unrelated applications
    if best_match and best_score >= 0.60:
        return best_match

    return None, None


def open_application(app_name):
    app_name = app_name.lower().strip()

    if not request_permission("open_application"):
        return "Permission denied."

    # Try command-line executable first
    executable = shutil.which(app_name)

    if executable:
        try:
            subprocess.Popen([executable])
            return f"Opening {app_name}."

        except OSError:
            pass

    # Search Windows Start-menu applications
    matched_name, app_id = find_application(app_name)

    if app_id:
        try:
            subprocess.Popen(
                [
                    "explorer.exe",
                    f"shell:AppsFolder\\{app_id}",
                ]
            )

            return f"Opening {matched_name}."

        except OSError:
            return (
                f"I found {matched_name}, "
                "but could not open it."
            )

    return (
        f"I couldn't find an application "
        f"called {app_name}."
    )


def close_application(app_name):
    app_name = app_name.lower().strip()

    # Resolve app name into Windows process name
    process_name = PROCESS_ALIASES.get(app_name)

    if not process_name:
        return (
            f"I don't know how to close "
            f"{app_name} yet."
        )

    # Closing apps requires confirmation
    allowed = request_permission(
        "close_application",
        f"Are you sure you want to close {app_name}?"
    )

    if not allowed:
        return "Action cancelled."

    try:
        result = subprocess.run(
            [
                "taskkill",
                "/IM",
                process_name,
                "/F",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return f"Closed {app_name}."

        return (
            f"I couldn't close {app_name}. "
            "It may not be running."
        )

    except OSError:
        return f"I couldn't close {app_name}."