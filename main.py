from commands.parser import process_command
from commands.normalizer import normalize_command

from database.database import create_tables
from database.history import save_command
from database.watcher import (
    start_index_watcher,
    stop_index_watcher,
)

from speech.recorder import record_audio
from speech.speech_to_text import transcribe_audio
from speech.text_to_speech import speak


WAKE_WORDS = [
    "voicepilot",
    "voice pilot",
]


SLEEP_COMMANDS = [
    "go to sleep",
    "sleep",
    "stop listening",
    "go idle",
]


def contains_wake_word(text):
    if not text:
        return False

    text = text.lower().strip()

    for wake_word in WAKE_WORDS:
        if wake_word in text:
            return True

    return False


def listen_and_transcribe():
    audio_path = record_audio()

    if not audio_path:
        return None

    print("Transcribing...")

    return transcribe_audio(
        audio_path
    )


def wait_for_wake_word():
    while True:
        print(
            "\nWaiting for wake word..."
        )

        print(
            "Say: VoicePilot"
        )

        text = listen_and_transcribe()

        if not text:
            continue

        print(
            f"Heard: {text}"
        )

        if contains_wake_word(text):
            print(
                "VoicePilot activated."
            )

            speak("Yes?")

            return


def listen_for_command():
    print(
        "\nListening for command..."
    )

    raw_command = (
        listen_and_transcribe()
    )

    if not raw_command:
        return None

    print(
        f"You said: {raw_command}"
    )

    command = normalize_command(
        raw_command
    )

    print(
        f"Normalized: {command}"
    )

    return command


def is_sleep_command(command):
    if not command:
        return False

    command = (
        command
        .lower()
        .strip()
    )

    return command in SLEEP_COMMANDS


def get_spoken_response(response):
    """
    Convert internal action responses
    into natural text-to-speech responses.
    """

    special_responses = {
        "LOCKED":
            "Locking your computer.",

        "RESTARTING":
            "Restarting your computer.",

        "SHUTTING_DOWN":
            "Shutting down your computer.",
    }

    return special_responses.get(
        response,
        response,
    )


def execute_command(
    raw_command,
    speak_result=True,
):
    """
    Execute a command through VoicePilot's
    existing command system.

    This function is reusable by:
    - terminal mode
    - desktop UI
    - future wake-word mode

    Returns a dictionary containing:
        command
        response
        spoken_response
        intent
        success
        exit
        sleep
    """

    if not raw_command:
        return {
            "command": "",
            "response":
                "No command detected.",
            "spoken_response":
                "No command detected.",
            "intent": None,
            "success": False,
            "exit": False,
            "sleep": False,
        }

    # ------------------------------------------
    # NORMALIZE
    # ------------------------------------------

    command = normalize_command(
        raw_command
    )

    print(
        f"Normalized: {command}"
    )

    if not command:
        return {
            "command": "",
            "response":
                "I couldn't understand "
                "that command.",
            "spoken_response":
                "I couldn't understand "
                "that command.",
            "intent": None,
            "success": False,
            "exit": False,
            "sleep": False,
        }

    # ------------------------------------------
    # SLEEP COMMAND
    # ------------------------------------------

    if is_sleep_command(command):
        response = "Going idle."

        if speak_result:
            speak(response)

        return {
            "command": command,
            "response": response,
            "spoken_response": response,
            "intent": "sleep",
            "success": True,
            "exit": False,
            "sleep": True,
        }

    # ------------------------------------------
    # PROCESS COMMAND
    # ------------------------------------------

    result = process_command(
        command
    )

    response = result.get(
        "response"
    )

    intent = result.get(
        "intent"
    )

    success = result.get(
        "success",
        False,
    )

    # ------------------------------------------
    # SAVE HISTORY
    # ------------------------------------------

    save_command(
        command=command,
        intent=intent,
        success=success,
    )

    # ------------------------------------------
    # EXIT
    # ------------------------------------------

    if response == "EXIT":
        return {
            "command": command,
            "response": "EXIT",
            "spoken_response": "Goodbye.",
            "intent": intent,
            "success": success,
            "exit": True,
            "sleep": False,
        }

    # ------------------------------------------
    # NATURAL SPOKEN RESPONSE
    # ------------------------------------------

    spoken_response = (
        get_spoken_response(
            response
        )
        if response
        else ""
    )

    if spoken_response:
        print(
            spoken_response
        )

        if speak_result:
            speak(
                spoken_response
            )

    return {
        "command": command,
        "response": response,
        "spoken_response":
            spoken_response,
        "intent": intent,
        "success": success,
        "exit": False,
        "sleep": False,
    }


def active_mode():
    """
    Keep accepting commands until the
    user tells VoicePilot to go to sleep.
    """

    print(
        "\nActive mode started."
    )

    print(
        "Say 'go to sleep' "
        "to return to idle mode."
    )

    while True:
        command = (
            listen_for_command()
        )

        if not command:
            print(
                "No command detected."
            )

            continue

        result = execute_command(
            command,
            speak_result=True,
        )

        if result["exit"]:
            return "EXIT"

        if result["sleep"]:
            print(
                "VoicePilot going idle."
            )

            return "SLEEP"


def main():
    # ----------------------------------------------
    # DATABASE
    # ----------------------------------------------

    create_tables()

    # ----------------------------------------------
    # START INDEX WATCHER
    # ----------------------------------------------

    observer = (
        start_index_watcher()
    )

    print(
        "VoicePilot started."
    )

    print(
        "Say 'VoicePilot' to activate."
    )

    try:
        while True:

            # --------------------------------------
            # IDLE MODE
            # --------------------------------------

            wait_for_wake_word()

            # --------------------------------------
            # ACTIVE MODE
            # --------------------------------------

            result = active_mode()

            if result == "EXIT":
                print(
                    "VoicePilot stopped."
                )

                speak(
                    "Goodbye."
                )

                break

    finally:
        # ------------------------------------------
        # ALWAYS STOP WATCHER CLEANLY
        # ------------------------------------------

        stop_index_watcher(
            observer
        )


if __name__ == "__main__":
    main()