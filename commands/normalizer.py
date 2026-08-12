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
    """

    if not command:
        return ""

    command = command.lower().strip()

    # Remove punctuation produced by speech recognition
    command = re.sub(r"[^\w\s]", "", command)

    # Replace known speech variations
    for phrase, replacement in PHRASE_REPLACEMENTS.items():
        command = command.replace(phrase, replacement)

    # Remove polite/filler phrases
    for filler in FILLER_PHRASES:
        command = command.replace(filler, "")

    command = command.strip()

    # Convert different action words into our standard "open" command
    if command.startswith("launch "):
        command = "open " + command[len("launch "):]

    elif command.startswith("start "):
        command = "open " + command[len("start "):]

    # Folder-navigation phrases
    if command.startswith("go to folder "):
        command = "open folder " + command[len("go to folder "):]

    elif command.startswith("go to "):
        command = "open folder " + command[len("go to "):]

    elif command.startswith("take me to "):
        command = "open folder " + command[len("take me to "):]

    # Handle:
    # "open the voicepilot folder"
    match = re.fullmatch(r"open the (.+) folder", command)

    if match:
        folder_name = match.group(1).strip()
        command = f"open folder {folder_name}"

    # Handle:
    # "open voicepilot folder"
    match = re.fullmatch(r"open (.+) folder", command)

    if match and not command.startswith("open folder "):
        folder_name = match.group(1).strip()
        command = f"open folder {folder_name}"

    # Remove repeated spaces
    command = re.sub(r"\s+", " ", command)

    return command.strip()