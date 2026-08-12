from faster_whisper import WhisperModel


print("Loading speech recognition model...")

model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

print("Speech recognition model loaded.")


def transcribe_audio(audio_path):
    """
    Convert an audio file into text using faster-whisper.
    """

    try:
        segments, info = model.transcribe(
            str(audio_path),
            language="en",
            beam_size=5
        )

        text_parts = []

        for segment in segments:
            text_parts.append(segment.text.strip())

        text = " ".join(text_parts).strip()

        if not text:
            return None

        return text

    except Exception as error:
        print(f"Speech recognition error: {error}")
        return None