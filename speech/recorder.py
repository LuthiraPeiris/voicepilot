import queue
from pathlib import Path

import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write


SAMPLE_RATE = 16000
CHANNELS = 1

AUDIO_FOLDER = Path("audio")
AUDIO_FILE = AUDIO_FOLDER / "command.wav"


# Length of each captured audio block.
BLOCK_DURATION = 0.1


# Stop recording after this amount
# of silence once speech has started.
SILENCE_DURATION = 1.0


# Maximum amount of time to listen
# after calibration.
MAX_DURATION = 10


# Amount of time used to measure
# background noise.
NOISE_CALIBRATION_DURATION = 0.6


# Prevent very quiet rooms from making
# the microphone too sensitive.
MIN_SILENCE_THRESHOLD = 250


# Background noise multiplier used to
# determine the speech threshold.
NOISE_MULTIPLIER = 2.5


def calculate_volume(block):
    """
    Calculate average absolute amplitude
    of an audio block.
    """

    block_float = block.astype(
        np.float32
    )

    return float(
        np.mean(
            np.abs(
                block_float
            )
        )
    )


def record_audio():
    """
    Record audio until the user stops
    speaking.

    Behaviour:
    - Calibrates current background noise
    - Detects when speech starts
    - Records until sustained silence
    - Stops after MAX_DURATION
    - Returns None if no speech is detected
    """

    AUDIO_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    audio_queue = queue.Queue()

    recorded_blocks = []
    calibration_blocks = []

    speech_started = False

    silence_time = 0.0
    total_time = 0.0
    calibration_time = 0.0

    silence_threshold = (
        MIN_SILENCE_THRESHOLD
    )

    print("Listening...")

    def callback(
        indata,
        frames,
        time,
        status,
    ):
        if status:
            print(
                f"Audio status: {status}"
            )

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

            # ----------------------------------
            # BACKGROUND NOISE CALIBRATION
            # ----------------------------------

            while (
                calibration_time
                < NOISE_CALIBRATION_DURATION
            ):
                block = (
                    audio_queue.get()
                )

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
                background_noise = 0.0

            silence_threshold = max(
                MIN_SILENCE_THRESHOLD,
                background_noise
                * NOISE_MULTIPLIER,
            )


            # ----------------------------------
            # RECORD SPEECH
            # ----------------------------------

            while (
                total_time
                < MAX_DURATION
            ):
                block = (
                    audio_queue.get()
                )

                volume = (
                    calculate_volume(
                        block
                    )
                )

                total_time += (
                    BLOCK_DURATION
                )

                if (
                    volume
                    > silence_threshold
                ):
                    speech_started = True
                    silence_time = 0.0

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

                # Stop once the user has
                # finished speaking.
                if (
                    speech_started
                    and silence_time
                    >= SILENCE_DURATION
                ):
                    break

        # --------------------------------------
        # NO SPEECH
        # --------------------------------------

        if not speech_started:
            print(
                "No speech detected."
            )

            return None

        if not recorded_blocks:
            print(
                "No audio recorded."
            )

            return None

        # --------------------------------------
        # SAVE AUDIO
        # --------------------------------------

        recording = np.concatenate(
            recorded_blocks,
            axis=0,
        )

        write(
            AUDIO_FILE,
            SAMPLE_RATE,
            recording,
        )

        print(
            "Recording completed."
        )

        return AUDIO_FILE

    except Exception as error:
        print(
            "Microphone error: "
            f"{error}"
        )

        return None