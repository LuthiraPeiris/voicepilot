import sounddevice as sd
from scipy.io.wavfile import write
from pathlib import Path


SAMPLE_RATE = 16000
CHANNELS = 1

AUDIO_FOLDER = Path("audio")
AUDIO_FILE = AUDIO_FOLDER / "command.wav"


def record_audio(duration=5):
    """
    Record microphone audio and save it as a WAV file.
    """

    AUDIO_FOLDER.mkdir(exist_ok=True)

    print(f"Listening for {duration} seconds...")

    try:
        recording = sd.rec(
            int(duration * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
        )

        sd.wait()

        write(
            AUDIO_FILE,
            SAMPLE_RATE,
            recording,
        )

        print("Recording completed.")

        return AUDIO_FILE

    except Exception as error:
        print(f"Microphone error: {error}")
        return None


if __name__ == "__main__":
    record_audio()