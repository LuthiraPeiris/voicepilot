from commands.parser import process_command
from database.database import create_tables
from speech.recorder import record_audio
from speech.speech_to_text import transcribe_audio


def main():
    create_tables()

    print("VoicePilot started.")
    print("Say a command after each listening prompt.")
    print("Say 'exit' to stop.")

    while True:
        audio_path = record_audio(duration=5)

        if not audio_path:
            print("Recording failed. Try again.")
            continue

        print("Transcribing...")

        command = transcribe_audio(audio_path)

        if not command:
            print("I couldn't understand what you said.")
            continue

        print(f"You said: {command}")

        result = process_command(command)

        if result == "EXIT":
            print("VoicePilot stopped.")
            break

        print(result)


if __name__ == "__main__":
    main()