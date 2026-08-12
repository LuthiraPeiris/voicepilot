from faster_whisper import WhisperModel


print(
    "Loading speech recognition model..."
)

model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

print(
    "Speech recognition model loaded."
)


def transcribe_audio(audio_path):
    """
    Convert an audio file into text using
    faster-whisper with Silero VAD filtering.
    """

    try:
        segments, info = model.transcribe(
            str(audio_path),
            language="en",
            beam_size=5,

            # Remove non-speech sections
            # before transcription.
            vad_filter=True,

            vad_parameters={
                "min_silence_duration_ms": 300,
            },
        )

        text_parts = []

        for segment in segments:
            text = segment.text.strip()

            if text:
                text_parts.append(
                    text
                )

        text = " ".join(
            text_parts
        ).strip()

        if not text:
            return None

        return text

    except Exception as error:
        print(
            "Speech recognition error: "
            f"{error}"
        )

        return None