import queue
from pathlib import Path

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write


SAMPLE_RATE = 16000
CHANNELS = 1

AUDIO_FOLDER = Path("audio")
AUDIO_FILE = AUDIO_FOLDER / "command.wav"

BLOCK_DURATION = 0.1
SILENCE_DURATION = 1.2
MAX_DURATION = 10

SILENCE_THRESHOLD = 500


def record_audio():
    """
    Record audio until the user stops speaking.

    Recording stops when:
    - speech has started, and
    - silence continues for SILENCE_DURATION seconds,
    - or MAX_DURATION is reached.
    """

    AUDIO_FOLDER.mkdir(exist_ok=True)

    audio_queue = queue.Queue()
    recorded_blocks = []

    speech_started = False
    silence_time = 0
    total_time = 0

    print("Listening...")

    def callback(indata, frames, time, status):
        if status:
            print(status)

        audio_queue.put(indata.copy())

    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=int(SAMPLE_RATE * BLOCK_DURATION),
            callback=callback,
        ):

            while total_time < MAX_DURATION:
                block = audio_queue.get()

                recorded_blocks.append(block)

                volume = np.abs(block).mean()

                total_time += BLOCK_DURATION

                # Speech detected
                if volume > SILENCE_THRESHOLD:
                    speech_started = True
                    silence_time = 0

                elif speech_started:
                    silence_time += BLOCK_DURATION

                # Stop after enough silence
                if (
                    speech_started
                    and silence_time >= SILENCE_DURATION
                ):
                    break

        if not recorded_blocks:
            print("No audio recorded.")
            return None

        if not speech_started:
            print("No speech detected.")
            return None

        recording = np.concatenate(
            recorded_blocks,
            axis=0
        )

        write(
            AUDIO_FILE,
            SAMPLE_RATE,
            recording
        )

        print("Recording completed.")

        return AUDIO_FILE

    except Exception as error:
        print(f"Microphone error: {error}")
        return None