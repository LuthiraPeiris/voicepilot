import re


PHRASE_REPLACEMENTS = {
    "vs code": "vscode",
    "visual studio code": "vscode",
    "voice pilot": "voicepilot",
    "git hub": "github",
}


FILLER_PHRASES = [
    "can you please",
    "could you please",
    "would you please",
    "can you",
    "could you",
    "would you",
    "please",
]


def normalize_command(command):
    """
    Clean speech-recognition output before sending it
    to the command parser.

    Important filename characters such as:
    . - _ \\ / :
    are preserved.
    """

    if not command:
        return ""

    command = command.lower().strip()

    # --------------------------------------------------
    # CONVERT SPOKEN FILE EXTENSION SEPARATOR
    #
    # Example:
    # example dot txt
    # -> example.txt
    # --------------------------------------------------

    command = re.sub(
        r"\s+dot\s+",
        ".",
        command,
    )

    # --------------------------------------------------
    # REMOVE UNNECESSARY PUNCTUATION
    #
    # Preserve characters useful in filenames/paths:
    # .  -  _  \  /  :
    # --------------------------------------------------

    command = re.sub(
        r"[^\w\s.\-\\/:]",
        "",
        command,
    )

    # --------------------------------------------------
    # KNOWN SPEECH VARIATIONS
    # --------------------------------------------------

    for phrase, replacement in PHRASE_REPLACEMENTS.items():
        command = command.replace(
            phrase,
            replacement,
        )

    # --------------------------------------------------
    # REMOVE POLITE / FILLER PHRASES
    # --------------------------------------------------

    for filler in FILLER_PHRASES:
        command = command.replace(
            filler,
            "",
        )

    command = command.strip()

    # --------------------------------------------------
    # NORMALIZE APPLICATION OPENING COMMANDS
    # --------------------------------------------------

    if command.startswith("launch "):
        command = (
            "open "
            + command[len("launch "):]
        )

    elif command.startswith("start "):
        command = (
            "open "
            + command[len("start "):]
        )

    # --------------------------------------------------
    # FOLDER NAVIGATION PHRASES
    # --------------------------------------------------

    if command.startswith("go to folder "):
        command = (
            "open folder "
            + command[len("go to folder "):]
        )

    elif command.startswith("go to "):
        command = (
            "open folder "
            + command[len("go to "):]
        )

    elif command.startswith("take me to "):
        command = (
            "open folder "
            + command[len("take me to "):]
        )

    # --------------------------------------------------
    # "open the voicepilot folder"
    # --------------------------------------------------

    match = re.fullmatch(
        r"open the (.+) folder",
        command,
    )

    if match:
        folder_name = (
            match.group(1).strip()
        )

        command = (
            f"open folder {folder_name}"
        )

    # --------------------------------------------------
    # "open voicepilot folder"
    # --------------------------------------------------

    match = re.fullmatch(
        r"open (.+) folder",
        command,
    )

    if (
        match
        and not command.startswith(
            "open folder "
        )
    ):
        folder_name = (
            match.group(1).strip()
        )

        command = (
            f"open folder {folder_name}"
        )

    # --------------------------------------------------
    # REMOVE REPEATED SPACES
    # --------------------------------------------------

    command = re.sub(
        r"\s+",
        " ",
        command,
    )

    # --------------------------------------------------
    # REMOVE SENTENCE-ENDING PERIODS
    #
    # Whisper may return:
    #
    # "go back."
    #
    # We need:
    #
    # "go back"
    #
    # But dots inside filenames are preserved:
    #
    # "create file example.txt."
    # -> "create file example.txt"
    # --------------------------------------------------

    command = command.rstrip(".")

    return command.strip()