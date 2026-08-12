import re

from speech.recorder import record_audio
from speech.speech_to_text import transcribe_audio
from speech.text_to_speech import speak


YES_RESPONSES = {
    "yes",
    "yeah",
    "yep",
    "confirm",
    "do it",
    "go ahead",
    "sure",
    "okay",
    "ok",
}

NO_RESPONSES = {
    "no",
    "nope",
    "cancel",
    "stop",
    "dont",
    "do not",
}


def normalize_confirmation(response):
    if not response:
        return ""

    response = response.lower().strip()

    # Remove punctuation such as:
    # "Yes." -> "yes"
    # "No!" -> "no"
    response = re.sub(r"[^\w\s]", "", response)

    # Remove repeated spaces
    response = re.sub(r"\s+", " ", response)

    return response.strip()


def ask_for_confirmation(message):
    speak(message)
    print(message)

    print("Waiting for confirmation...")

    audio_path = record_audio()

    if not audio_path:
        speak("I couldn't hear your response.")
        return False

    response = transcribe_audio(audio_path)

    if not response:
        speak("I couldn't understand your response.")
        return False

    print(f"Raw confirmation response: {response}")

    response = normalize_confirmation(response)

    print(f"Normalized confirmation: {response}")

    if response in YES_RESPONSES:
        return True

    if response in NO_RESPONSES:
        return False

    speak("Confirmation not recognized. Action cancelled.")

    return False