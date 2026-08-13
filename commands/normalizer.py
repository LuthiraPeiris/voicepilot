import re
from difflib import SequenceMatcher


# --------------------------------------------------
# KNOWN PHRASE REPLACEMENTS
# --------------------------------------------------

PHRASE_REPLACEMENTS = {
    "vs code": "vscode",
    "visual studio code": "vscode",
    "voice pilot": "voicepilot",
    "git hub": "github",

    # Common command variations
    "shut down": "shutdown",
    "re name": "rename",
}


# --------------------------------------------------
# FILLER / POLITE PHRASES
# --------------------------------------------------

FILLER_PHRASES = [
    "can you please",
    "could you please",
    "would you please",
    "can you",
    "could you",
    "would you",
    "please",
]


# --------------------------------------------------
# VALID VOICEPILOT COMMAND VERBS
# --------------------------------------------------

COMMAND_VERBS = {
    "open",
    "close",
    "create",
    "delete",
    "rename",
    "refresh",
    "restart",
    "shutdown",
    "lock",
    "mute",
    "unmute",
    "increase",
    "decrease",
    "raise",
    "lower",
    "turn",
    "go",
}


# --------------------------------------------------
# WORDS THAT HELP US DETERMINE COMMAND CONTEXT
# --------------------------------------------------

FILE_FOLDER_WORDS = {
    "file",
    "folder",
}


# --------------------------------------------------
# COMMON SPEECH-TO-TEXT COMMAND MISTAKES
# --------------------------------------------------
#
# These are deliberately limited.
#
# We do NOT want to aggressively replace random
# words because VoicePilot may be handling actual
# filenames and folder names.
# --------------------------------------------------

COMMAND_WORD_CORRECTIONS = {
    # DELETE
    "the lead": "delete",
    "delight": "delete",
    "deleted": "delete",
    "deleet": "delete",
    "relief": "delete",

    # RENAME
    "remain": "rename",
    "renamed": "rename",

    # CREATE
    "creator": "create",

    # OPEN
    "opened": "open",

    # CLOSE
    "closed": "close",

    # RESTART
    "re start": "restart",

    # SHUTDOWN
    "shutdown": "shutdown",
}


# --------------------------------------------------
# COMMAND VERB SIMILARITY
# --------------------------------------------------

COMMAND_SIMILARITY_THRESHOLD = 0.72


def similarity(first, second):
    """
    Calculate similarity between
    two strings.
    """

    return SequenceMatcher(
        None,
        first,
        second,
    ).ratio()


def correct_known_command_phrase(command):
    """
    Correct known speech-recognition errors
    at the beginning of a command.

    Example:

        relief folder example

    becomes:

        delete folder example

    Only the command portion is corrected.
    Filenames/folder names are left untouched.
    """

    words = command.split()

    if not words:
        return command

    # --------------------------------------------------
    # CHECK TWO-WORD COMMAND MISTAKES FIRST
    # --------------------------------------------------

    if len(words) >= 2:
        first_two = (
            f"{words[0]} {words[1]}"
        )

        if first_two in COMMAND_WORD_CORRECTIONS:
            corrected = (
                COMMAND_WORD_CORRECTIONS[
                    first_two
                ]
            )

            remaining = " ".join(
                words[2:]
            )

            if remaining:
                return (
                    f"{corrected} "
                    f"{remaining}"
                )

            return corrected

    # --------------------------------------------------
    # CHECK FIRST WORD AGAINST KNOWN MISTAKES
    # --------------------------------------------------

    first_word = words[0]

    if first_word in COMMAND_WORD_CORRECTIONS:
        words[0] = (
            COMMAND_WORD_CORRECTIONS[
                first_word
            ]
        )

        return " ".join(words)

    return command


def correct_command_verb_from_context(
    command,
):
    """
    Try to recover the intended first command
    word when speech-to-text gives us something
    invalid.

    This correction is intentionally conservative.

    Example:

        relief folder example

    The first word is not a VoicePilot command,
    but the second word is "folder".

    VoicePilot can safely consider known command
    verbs such as:

        open folder
        close folder
        create folder
        delete folder
        rename folder

    and find the closest likely verb.

    We do NOT modify filenames or folder names.
    """

    words = command.split()

    if len(words) < 2:
        return command

    first_word = words[0]

    # Already valid.
    if first_word in COMMAND_VERBS:
        return command

    second_word = words[1]

    # For now, automatic fuzzy correction is only
    # used when the following word gives us a strong
    # command context such as file/folder.
    if second_word not in FILE_FOLDER_WORDS:
        return command

    contextual_verbs = {
        "open",
        "close",
        "create",
        "delete",
        "rename",
    }

    best_verb = None
    best_score = 0

    for verb in contextual_verbs:
        score = similarity(
            first_word,
            verb,
        )

        if score > best_score:
            best_score = score
            best_verb = verb

    if (
        best_verb
        and best_score
        >= COMMAND_SIMILARITY_THRESHOLD
    ):
        original = first_word

        words[0] = best_verb

        corrected_command = " ".join(
            words
        )

        print(
            "Command correction: "
            f"'{original}' -> "
            f"'{best_verb}'"
        )

        return corrected_command

    return command


def normalize_command(command):
    """
    Clean speech-recognition output before
    sending it to the command parser.

    VoicePilot uses two command-recognition
    layers:

    1. Whisper speech recognition
    2. VoicePilot command-aware normalization

    Important filename characters such as:

        . - _ \\ / :

    are preserved.
    """

    if not command:
        return ""

    command = (
        command
        .lower()
        .strip()
    )

    # --------------------------------------------------
    # CONVERT SPOKEN FILE EXTENSION SEPARATOR
    #
    # example dot txt
    # ->
    # example.txt
    # --------------------------------------------------

    command = re.sub(
        r"\s+dot\s+",
        ".",
        command,
    )

    # --------------------------------------------------
    # REMOVE UNNECESSARY PUNCTUATION
    #
    # Preserve useful filename/path characters:
    #
    # . - _ \ / :
    # --------------------------------------------------

    command = re.sub(
        r"[^\w\s.\-\\/:]",
        "",
        command,
    )

    # --------------------------------------------------
    # REMOVE REPEATED SPACES EARLY
    # --------------------------------------------------

    command = re.sub(
        r"\s+",
        " ",
        command,
    ).strip()

    # --------------------------------------------------
    # KNOWN SPEECH VARIATIONS
    # --------------------------------------------------

    for (
        phrase,
        replacement,
    ) in PHRASE_REPLACEMENTS.items():

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

    command = re.sub(
        r"\s+",
        " ",
        command,
    ).strip()

    # --------------------------------------------------
    # COMMAND-SPECIFIC SPEECH CORRECTION
    # --------------------------------------------------

    command = correct_known_command_phrase(
        command
    )

    command = (
        correct_command_verb_from_context(
            command
        )
    )

    # --------------------------------------------------
    # NORMALIZE APPLICATION OPENING COMMANDS
    # --------------------------------------------------

    if command.startswith(
        "launch "
    ):
        command = (
            "open "
            + command[
                len("launch "):
            ]
        )

    elif command.startswith(
        "start "
    ):
        command = (
            "open "
            + command[
                len("start "):
            ]
        )

    # --------------------------------------------------
    # FOLDER NAVIGATION
    # --------------------------------------------------

    if command.startswith(
        "go to folder "
    ):
        command = (
            "open folder "
            + command[
                len("go to folder "):
            ]
        )

    elif command.startswith(
        "go to "
    ):
        command = (
            "open folder "
            + command[
                len("go to "):
            ]
        )

    elif command.startswith(
        "take me to "
    ):
        command = (
            "open folder "
            + command[
                len("take me to "):
            ]
        )

    # --------------------------------------------------
    # "open the voicepilot folder"
    #
    # ->
    #
    # "open folder voicepilot"
    # --------------------------------------------------

    match = re.fullmatch(
        r"open the (.+) folder",
        command,
    )

    if match:
        folder_name = (
            match
            .group(1)
            .strip()
        )

        command = (
            f"open folder "
            f"{folder_name}"
        )

    # --------------------------------------------------
    # "open voicepilot folder"
    #
    # ->
    #
    # "open folder voicepilot"
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
            match
            .group(1)
            .strip()
        )

        command = (
            f"open folder "
            f"{folder_name}"
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
    # REMOVE SENTENCE-ENDING PERIOD
    #
    # Whisper:
    #
    # go back.
    #
    # ->
    #
    # go back
    #
    # Dots inside filenames remain:
    #
    # create file example.txt.
    #
    # ->
    #
    # create file example.txt
    # --------------------------------------------------

    command = command.rstrip(".")

    return command.strip()