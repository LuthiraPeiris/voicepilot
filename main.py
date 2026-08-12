from commands.parser import process_command
from commands.normalizer import normalize_command
from database.database import create_tables
from speech.recorder import record_audio
from speech.speech_to_text import transcribe_audio
from speech.text_to_speech import speak


def main():
    create_tables()

    print("VoicePilot started.")
    print("Say a command after each listening prompt.")
    print("Say 'exit' to stop.")


    while True:
        audio_path = record_audio()

        if not audio_path:
            print("Recording failed. Try again.")
            speak("Recording failed.")
            continue

        print("Transcribing...")

        raw_command = transcribe_audio(audio_path)

        if not raw_command:
            message = "I couldn't understand what you said."

            print(message)
            speak(message)

            continue

        print(f"You said: {raw_command}")

        command = normalize_command(raw_command)

        print(f"Normalized: {command}")

        result = process_command(command)

        if result == "EXIT":
            print("VoicePilot stopped.")
            speak("VoicePilot stopped.")
            break

        print(result)
        speak(result)


if __name__ == "__main__":
    main()