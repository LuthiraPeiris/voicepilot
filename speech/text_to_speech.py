import pyttsx3


engine = pyttsx3.init()


def speak(text):
    """
    Speak text using the Windows text-to-speech engine.
    """

    if not text:
        return

    try:
        engine.say(text)
        engine.runAndWait()

    except Exception as error:
        print(f"Text-to-speech error: {error}")