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
SILENCE_DURATION = 1.0
MAX_DURATION = 10

# How long VoicePilot listens to the room
# before deciding what "background noise" sounds like.
NOISE_CALIBRATION_DURATION = 0.6

# Minimum threshold so very quiet rooms
# don't become overly sensitive.
MIN_SILENCE_THRESHOLD = 250

# Background noise multiplier.
NOISE_MULTIPLIER = 2.5


def calculate_volume(block):
    """
    Calculate the average absolute amplitude
    of an audio block.
    """

    block_float = block.astype(np.float32)

    return float(
        np.mean(
            np.abs(block_float)
        )
    )


def record_audio():
    """
    Record audio until the user stops speaking.

    Improvements:
    - Measures current background noise automatically
    - Uses an adaptive speech threshold
    - Stops after sustained silence
    - Prevents very long recordings
    """

    AUDIO_FOLDER.mkdir(exist_ok=True)

    audio_queue = queue.Queue()

    recorded_blocks = []
    calibration_blocks = []

    speech_started = False

    silence_time = 0.0
    total_time = 0.0
    calibration_time = 0.0

    silence_threshold = MIN_SILENCE_THRESHOLD

    print("Listening...")

    def callback(
        indata,
        frames,
        time,
        status
    ):
        if status:
            print(status)

        audio_queue.put(
            indata.copy()
        )

    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="int16",
            blocksize=int(
                SAMPLE_RATE
                * BLOCK_DURATION
            ),
            callback=callback,
        ):

            # ------------------------------------------
            # CALIBRATE BACKGROUND NOISE
            # ------------------------------------------

            while (
                calibration_time
                < NOISE_CALIBRATION_DURATION
            ):
                block = audio_queue.get()

                calibration_blocks.append(
                    block
                )

                calibration_time += (
                    BLOCK_DURATION
                )

            noise_levels = [
                calculate_volume(block)
                for block
                in calibration_blocks
            ]

            if noise_levels:
                background_noise = float(
                    np.median(
                        noise_levels
                    )
                )
            else:
                background_noise = 0

            silence_threshold = max(
                MIN_SILENCE_THRESHOLD,
                background_noise
                * NOISE_MULTIPLIER,
            )

            # ------------------------------------------
            # RECORD COMMAND
            # ------------------------------------------

            while total_time < MAX_DURATION:
                block = audio_queue.get()

                volume = calculate_volume(
                    block
                )

                total_time += BLOCK_DURATION

                if volume > silence_threshold:
                    speech_started = True
                    silence_time = 0

                    recorded_blocks.append(
                        block
                    )

                elif speech_started:
                    recorded_blocks.append(
                        block
                    )

                    silence_time += (
                        BLOCK_DURATION
                    )

                # Stop after the user has
                # stopped speaking.
                if (
                    speech_started
                    and silence_time
                    >= SILENCE_DURATION
                ):
                    break

        if not speech_started:
            print("No speech detected.")
            return None

        if not recorded_blocks:
            print("No audio recorded.")
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
        print(
            f"Microphone error: {error}"
        )

        return None