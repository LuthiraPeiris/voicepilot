import re

from speech.recorder import record_audio
from speech.speech_to_text import transcribe_audio
from speech.text_to_speech import speak


YES_RESPONSES = {
    "yes",
    "yeah",
    "yep",
    "yup",
    "confirm",
    "confirmed",
    "do it",
    "go ahead",
    "sure",
    "okay",
    "ok",
    "proceed",
    "continue",
    "please do",
    "yes please",
}


NO_RESPONSES = {
    "no",
    "nope",
    "nah",
    "cancel",
    "cancel it",
    "stop",
    "dont",
    "do not",
    "dont do it",
    "do not do it",
    "never mind",
    "nevermind",
    "abort",
}


YES_WORDS = {
    "yes",
    "yeah",
    "yep",
    "yup",
    "sure",
    "confirm",
    "confirmed",
    "proceed",
}


NO_WORDS = {
    "no",
    "nope",
    "nah",
    "cancel",
    "stop",
    "abort",
}


MAX_CONFIRMATION_ATTEMPTS = 2


def normalize_confirmation(response):
    """
    Normalize a spoken confirmation response.

    Examples:
        "Yes!" -> "yes"
        "Yeah, do it." -> "yeah do it"
        "Don't do it." -> "dont do it"
    """

    if not response:
        return ""

    response = response.lower().strip()

    # Normalize curly apostrophes.
    response = response.replace("’", "'")

    # Convert common contractions before
    # punctuation is removed.
    response = response.replace(
        "don't",
        "dont",
    )

    # Remove punctuation.
    response = re.sub(
        r"[^\w\s]",
        "",
        response,
    )

    # Remove repeated whitespace.
    response = re.sub(
        r"\s+",
        " ",
        response,
    )

    return response.strip()


def classify_confirmation(response):
    """
    Decide whether a normalized response
    means YES, NO, or is UNKNOWN.

    Returns:
        True  -> confirmed
        False -> rejected
        None  -> unclear
    """

    response = normalize_confirmation(
        response
    )

    if not response:
        return None

    # --------------------------------------
    # EXACT MATCH
    # --------------------------------------

    if response in YES_RESPONSES:
        return True

    if response in NO_RESPONSES:
        return False

    # --------------------------------------
    # IMPORTANT NEGATIVE PHRASES
    # --------------------------------------

    negative_phrases = (
        "never mind",
        "nevermind",
        "dont do",
        "do not",
        "cancel",
        "stop",
        "abort",
    )

    for phrase in negative_phrases:
        if phrase in response:
            return False

    # --------------------------------------
    # COMMON POSITIVE PHRASES
    # --------------------------------------

    positive_phrases = (
        "go ahead",
        "do it",
        "please do",
        "you can",
        "continue",
        "proceed",
    )

    for phrase in positive_phrases:
        if phrase in response:
            return True

    # --------------------------------------
    # WORD-BASED MATCHING
    # --------------------------------------

    words = set(
        response.split()
    )

    # Negative takes priority for safety.
    if words.intersection(NO_WORDS):
        return False

    if words.intersection(YES_WORDS):
        return True

    return None


def listen_for_confirmation():
    """
    Record and transcribe a spoken
    confirmation response.

    Returns:
        transcription string
        or None if recording/transcription
        failed.
    """

    print(
        "Waiting for confirmation..."
    )

    audio_path = record_audio()

    if not audio_path:
        print(
            "No confirmation audio received."
        )

        return None

    response = transcribe_audio(
        audio_path
    )

    if not response:
        print(
            "Could not transcribe "
            "confirmation."
        )

        return None

    print(
        "Raw confirmation response: "
        f"{response}"
    )

    normalized = normalize_confirmation(
        response
    )

    print(
        "Normalized confirmation: "
        f"{normalized}"
    )

    return response


def ask_for_confirmation(
    message,
    max_attempts=MAX_CONFIRMATION_ATTEMPTS,
):
    """
    Ask the user for confirmation using
    speech.

    The user gets a limited number of
    attempts.

    Any failure eventually defaults to
    False so destructive actions are never
    performed accidentally.
    """

    speak(message)
    print(message)

    for attempt in range(
        1,
        max_attempts + 1,
    ):
        response = (
            listen_for_confirmation()
        )

        if response:
            result = classify_confirmation(
                response
            )

            if result is True:
                print(
                    "Confirmation accepted."
                )

                return True

            if result is False:
                print(
                    "Confirmation rejected."
                )

                speak(
                    "Okay. Action cancelled."
                )

                return False

        # ----------------------------------
        # RETRY
        # ----------------------------------

        if attempt < max_attempts:
            retry_message = (
                "I didn't catch a clear "
                "confirmation. "
                "Please say yes to continue "
                "or no to cancel."
            )

            print(retry_message)

            speak(retry_message)

    # --------------------------------------
    # FAIL SAFE
    # --------------------------------------

    cancel_message = (
        "Confirmation was not recognized. "
        "Action cancelled."
    )

    print(cancel_message)

    speak(cancel_message)

    return False