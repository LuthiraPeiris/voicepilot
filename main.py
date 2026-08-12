from commands.parser import process_command
from commands.normalizer import normalize_command
from database.database import create_tables
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


def active_mode():
    """
    Keep accepting commands until the user tells
    VoicePilot to go to sleep.
    """

    print("\nActive mode started.")
    print("Say 'go to sleep' to return to idle mode.")

    while True:
        command = listen_for_command()

        if not command:
            print("No command detected.")
            continue

        # Return to wake-word mode
        if is_sleep_command(command):
            print("VoicePilot going idle.")
            speak("Going idle.")
            return "SLEEP"

        # Completely close VoicePilot
        result = process_command(command)

        if result == "EXIT":
            return "EXIT"

        print(result)
        speak(result)


def main():
    create_tables()

    print("VoicePilot started.")
    print("Say 'VoicePilot' to activate.")

    while True:

        # Idle mode
        wait_for_wake_word()

        # Active conversational mode
        result = active_mode()

        if result == "EXIT":
            print("VoicePilot stopped.")
            speak("Goodbye.")
            break


if __name__ == "__main__":
    main()