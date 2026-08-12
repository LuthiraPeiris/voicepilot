from speech.recorder import record_audio
from speech.speech_to_text import transcribe_audio


def main():
    audio_path = record_audio(duration=5)

    if not audio_path:
        print("Recording failed.")
        return

    print("Transcribing...")

    text = transcribe_audio(audio_path)

    if text:
        print(f"You said: {text}")
    else:
        print("I couldn't understand what you said.")


if __name__ == "__main__":
    main()