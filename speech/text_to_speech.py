import threading

import pyttsx3


# Prevent multiple VoicePilot speech requests
# from trying to speak at the same time.
speech_lock = threading.Lock()


def speak(text):
    """
    Speak text using the Windows
    text-to-speech engine.

    A new pyttsx3 engine is created for
    every speech request.

    This is more reliable when VoicePilot
    commands are running from background
    threads in the desktop UI.
    """

    if not text:
        return

    text = str(text).strip()

    if not text:
        return

    try:
        with speech_lock:
            engine = pyttsx3.init()

            engine.say(text)

            engine.runAndWait()

            engine.stop()

    except Exception as error:
        print(
            "Text-to-speech error: "
            f"{error}"
        )