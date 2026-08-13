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

    return transcribe_audio(audio_path)


def wait_for_wake_word():
    while True:
        print("\nWaiting for wake word...")
        print("Say: VoicePilot")

        text = listen_and_transcribe()

        if not text:
            continue

        print(f"Heard: {text}")

        if contains_wake_word(text):
            print("VoicePilot activated.")
            speak("Yes?")
            return


def listen_for_command():
    print("\nListening for command...")

    raw_command = listen_and_transcribe()

    if not raw_command:
        return None

    print(f"You said: {raw_command}")

    command = normalize_command(raw_command)

    print(f"Normalized: {command}")

    return command


def is_sleep_command(command):
    command = command.lower().strip()

    return command in SLEEP_COMMANDS


def get_spoken_response(response):
    """
    Convert internal action responses into
    natural responses for text-to-speech.
    """

    special_responses = {
        "LOCKED": "Locking your computer.",
        "RESTARTING": "Restarting your computer.",
        "SHUTTING_DOWN": "Shutting down your computer.",
    }

    return special_responses.get(
        response,
        response,
    )


def active_mode():
    """
    Keep accepting commands until the user tells
    VoicePilot to go to sleep.
    """

    print("\nActive mode started.")
    print(
        "Say 'go to sleep' "
        "to return to idle mode."
    )

    while True:
        command = listen_for_command()

        if not command:
            print("No command detected.")
            continue

        # ------------------------------------------
        # RETURN TO WAKE-WORD MODE
        # ------------------------------------------

        if is_sleep_command(command):
            print("VoicePilot going idle.")
            speak("Going idle.")

            return "SLEEP"

        # ------------------------------------------
        # PROCESS COMMAND
        # ------------------------------------------

        result = process_command(
            command
        )

        response = result["response"]
        intent = result["intent"]
        success = result["success"]

        # ------------------------------------------
        # SAVE COMMAND HISTORY
        # ------------------------------------------

        save_command(
            command=command,
            intent=intent,
            success=success,
        )

        # ------------------------------------------
        # COMPLETELY CLOSE VOICEPILOT
        # ------------------------------------------

        if response == "EXIT":
            return "EXIT"

        # ------------------------------------------
        # SPEAK RESPONSE
        # ------------------------------------------

        if response:
            spoken_response = (
                get_spoken_response(
                    response
                )
            )

            print(spoken_response)

            speak(
                spoken_response
            )


def main():
    # ----------------------------------------------
    # DATABASE
    # ----------------------------------------------

    create_tables()

    # ----------------------------------------------
    # START AUTOMATIC FILE/FOLDER INDEX WATCHER
    # ----------------------------------------------

    observer = (
        start_index_watcher()
    )

    print("VoicePilot started.")
    print("Say 'VoicePilot' to activate.")

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

                speak("Goodbye.")

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