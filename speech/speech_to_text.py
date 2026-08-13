from faster_whisper import WhisperModel


print(
    "Loading speech recognition model..."
)


model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8",
)


print(
    "Speech recognition model loaded."
)


def transcribe_audio(audio_path):
    """
    Convert an audio file into text using
    faster-whisper.

    Silero VAD removes most non-speech
    sections before transcription.
    """

    if not audio_path:
        return None

    try:
        segments, info = model.transcribe(
            str(audio_path),

            language="en",

            beam_size=5,

            vad_filter=True,

            vad_parameters={
                "min_silence_duration_ms": 300,
            },
        )

        text_parts = []

        for segment in segments:
            text = (
                segment.text
                .strip()
            )

            if text:
                text_parts.append(
                    text
                )

        text = " ".join(
            text_parts
        ).strip()

        if not text:
            print(
                "No speech could be "
                "transcribed."
            )

            return None

        print(
            f"Transcription: {text}"
        )

        return text

    except Exception as error:
        print(
            "Speech recognition error: "
            f"{error}"
        )

        return None