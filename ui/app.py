import threading

import customtkinter as ctk

from main import execute_command

from database.database import create_tables
from database.watcher import (
    start_index_watcher,
    stop_index_watcher,
)

from speech.recorder import record_audio
from speech.speech_to_text import (
    transcribe_audio,
)


# --------------------------------------------------
# APPEARANCE
# --------------------------------------------------

ctk.set_appearance_mode("dark")

ctk.set_default_color_theme(
    "blue"
)


class VoicePilotApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ------------------------------------------
        # WINDOW
        # ------------------------------------------

        self.title(
            "VoicePilot"
        )

        # Always keep VoicePilot above
        # normal desktop windows.
        self.attributes(
            "-topmost",
            True,
        )

        self.geometry(
            "500x650"
        )

        self.minsize(
            450,
            550,
        )

        self.center_window()

        self.is_listening = False

        # ------------------------------------------
        # DATABASE
        # ------------------------------------------

        create_tables()

        # ------------------------------------------
        # FILE INDEX WATCHER
        # ------------------------------------------

        self.index_observer = (
            start_index_watcher()
        )

        # Handle window close safely.
        self.protocol(
            "WM_DELETE_WINDOW",
            self.close_application,
        )

        # ------------------------------------------
        # MAIN CONTAINER
        # ------------------------------------------

        self.main_frame = ctk.CTkFrame(
            self,
            corner_radius=20,
        )

        self.main_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20,
        )

        # ------------------------------------------
        # TITLE
        # ------------------------------------------

        self.title_label = (
            ctk.CTkLabel(
                self.main_frame,
                text="VoicePilot",
                font=ctk.CTkFont(
                    size=30,
                    weight="bold",
                ),
            )
        )

        self.title_label.pack(
            pady=(
                30,
                5,
            )
        )

        # ------------------------------------------
        # SUBTITLE
        # ------------------------------------------

        self.subtitle_label = (
            ctk.CTkLabel(
                self.main_frame,
                text=(
                    "Your desktop "
                    "voice assistant"
                ),
                font=ctk.CTkFont(
                    size=14,
                ),
                text_color="gray70",
            )
        )

        self.subtitle_label.pack(
            pady=(
                0,
                25,
            )
        )

        # ------------------------------------------
        # MICROPHONE AREA
        # ------------------------------------------

        self.mic_frame = (
            ctk.CTkFrame(
                self.main_frame,
                fg_color="transparent",
            )
        )

        self.mic_frame.pack(
            fill="x",
            pady=(
                5,
                15,
            ),
        )

        self.mic_button = (
            ctk.CTkButton(
                self.mic_frame,
                text="🎤",
                width=130,
                height=130,
                corner_radius=65,
                font=ctk.CTkFont(
                    size=48,
                ),
                command=(
                    self.handle_mic_click
                ),
            )
        )

        self.mic_button.pack(
            pady=10,
        )

        # ------------------------------------------
        # LISTEN LABEL
        # ------------------------------------------

        self.listen_label = (
            ctk.CTkLabel(
                self.mic_frame,
                text="Start Listening",
                font=ctk.CTkFont(
                    size=18,
                    weight="bold",
                ),
            )
        )

        self.listen_label.pack(
            pady=(
                5,
                10,
            )
        )

        # ------------------------------------------
        # COMMAND DISPLAY
        # ------------------------------------------

        self.command_frame = (
            ctk.CTkFrame(
                self.main_frame,
                corner_radius=12,
            )
        )

        self.command_frame.pack(
            fill="x",
            padx=25,
            pady=(
                5,
                10,
            ),
        )

        self.command_title = (
            ctk.CTkLabel(
                self.command_frame,
                text=(
                    "Recognized Command"
                ),
                font=ctk.CTkFont(
                    size=13,
                    weight="bold",
                ),
                text_color="gray70",
            )
        )

        self.command_title.pack(
            anchor="w",
            padx=15,
            pady=(
                12,
                5,
            ),
        )

        self.command_label = (
            ctk.CTkLabel(
                self.command_frame,
                text="No command yet",
                font=ctk.CTkFont(
                    size=16,
                ),
                wraplength=380,
                justify="left",
            )
        )

        self.command_label.pack(
            anchor="w",
            padx=15,
            pady=(
                0,
                15,
            ),
        )

        # ------------------------------------------
        # RESPONSE DISPLAY
        # ------------------------------------------

        self.response_frame = (
            ctk.CTkFrame(
                self.main_frame,
                corner_radius=12,
            )
        )

        self.response_frame.pack(
            fill="x",
            padx=25,
            pady=(
                0,
                10,
            ),
        )

        self.response_title = (
            ctk.CTkLabel(
                self.response_frame,
                text="VoicePilot",
                font=ctk.CTkFont(
                    size=13,
                    weight="bold",
                ),
                text_color="gray70",
            )
        )

        self.response_title.pack(
            anchor="w",
            padx=15,
            pady=(
                12,
                5,
            ),
        )

        self.response_label = (
            ctk.CTkLabel(
                self.response_frame,
                text="Ready for a command.",
                font=ctk.CTkFont(
                    size=15,
                ),
                wraplength=380,
                justify="left",
            )
        )

        self.response_label.pack(
            anchor="w",
            padx=15,
            pady=(
                0,
                15,
            ),
        )

        # ------------------------------------------
        # STATUS
        # ------------------------------------------

        self.status_label = (
            ctk.CTkLabel(
                self.main_frame,
                text="● Ready",
                font=ctk.CTkFont(
                    size=14,
                ),
            )
        )

        self.status_label.pack(
            pady=(
                5,
                20,
            )
        )

    # --------------------------------------------------
    # MICROPHONE
    # --------------------------------------------------

    def handle_mic_click(self):
        """
        Start VoicePilot listening when
        the microphone button is clicked.
        """

        if self.is_listening:
            return

        self.is_listening = True

        self.status_label.configure(
            text="● Listening..."
        )

        self.listen_label.configure(
            text="Listening..."
        )

        self.mic_button.configure(
            state="disabled"
        )

        self.command_label.configure(
            text=(
                "Listening for "
                "your command..."
            )
        )

        self.response_label.configure(
            text="..."
        )

        worker_thread = (
            threading.Thread(
                target=(
                    self.listen_and_process
                ),
                daemon=True,
            )
        )

        worker_thread.start()

    # --------------------------------------------------
    # LISTEN + TRANSCRIBE + EXECUTE
    # --------------------------------------------------

    def listen_and_process(self):
        """
        Complete VoicePilot command flow:

        microphone
        -> transcription
        -> normalization
        -> parser
        -> action
        -> response
        """

        audio_path = record_audio()

        if not audio_path:
            self.after(
                0,
                self.handle_no_audio,
            )

            return

        self.after(
            0,
            self.show_processing_status,
        )

        command_text = (
            transcribe_audio(
                audio_path
            )
        )

        if not command_text:
            self.after(
                0,
                self.handle_bad_transcription,
            )

            return

        print(
            "Recognized command: "
            f"{command_text}"
        )

        self.after(
            0,
            self.show_recognized_command,
            command_text,
        )

        # ------------------------------------------
        # EXECUTE EXISTING VOICEPILOT COMMAND
        # ------------------------------------------

        result = execute_command(
            command_text,
            speak_result=True,
        )

        self.after(
            0,
            self.command_finished,
            result,
        )

    # --------------------------------------------------
    # PROCESSING STATUS
    # --------------------------------------------------

    def show_processing_status(self):
        self.status_label.configure(
            text="● Processing..."
        )

        self.listen_label.configure(
            text="Processing..."
        )

    # --------------------------------------------------
    # SHOW TRANSCRIPTION
    # --------------------------------------------------

    def show_recognized_command(
        self,
        command_text,
    ):
        self.command_label.configure(
            text=command_text
        )

        self.status_label.configure(
            text="● Executing..."
        )

        self.listen_label.configure(
            text="Executing..."
        )

    # --------------------------------------------------
    # COMMAND COMPLETE
    # --------------------------------------------------

    def command_finished(
        self,
        result,
    ):
        self.is_listening = False

        self.mic_button.configure(
            state="normal"
        )

        # Prefer the natural spoken response.
        response = result.get(
            "spoken_response"
        )

        if not response:
            response = result.get(
                "response"
            )

        if response == "EXIT":
            response = "Goodbye."

        if not response:
            response = (
                "Command completed."
            )

        self.response_label.configure(
            text=response
        )

        self.status_label.configure(
            text="● Ready"
        )

        self.listen_label.configure(
            text="Start Listening"
        )

        # ------------------------------------------
        # EXIT VOICEPILOT
        # ------------------------------------------

        if result.get("exit"):
            self.after(
                500,
                self.close_application,
            )

    # --------------------------------------------------
    # NO AUDIO
    # --------------------------------------------------

    def handle_no_audio(self):
        self.is_listening = False

        self.mic_button.configure(
            state="normal"
        )

        self.command_label.configure(
            text="No speech detected."
        )

        self.response_label.configure(
            text=(
                "I couldn't hear "
                "anything."
            )
        )

        self.status_label.configure(
            text="● No speech detected"
        )

        self.listen_label.configure(
            text="Try Again"
        )

    # --------------------------------------------------
    # TRANSCRIPTION FAILURE
    # --------------------------------------------------

    def handle_bad_transcription(
        self,
    ):
        self.is_listening = False

        self.mic_button.configure(
            state="normal"
        )

        self.command_label.configure(
            text=(
                "I couldn't understand "
                "what you said."
            )
        )

        self.response_label.configure(
            text=(
                "Please try the "
                "command again."
            )
        )

        self.status_label.configure(
            text="● Try again"
        )

        self.listen_label.configure(
            text="Try Again"
        )

    # --------------------------------------------------
    # WINDOW POSITION
    # --------------------------------------------------

    def center_window(self):
        """
        Center VoicePilot on screen.
        """

        self.update_idletasks()

        width = 500
        height = 650

        screen_width = (
            self.winfo_screenwidth()
        )

        screen_height = (
            self.winfo_screenheight()
        )

        x = (
            screen_width - width
        ) // 2

        y = (
            screen_height - height
        ) // 2

        self.geometry(
            f"{width}x{height}"
            f"+{x}+{y}"
        )

    # --------------------------------------------------
    # CLOSE APPLICATION
    # --------------------------------------------------

    def close_application(self):
        """
        Stop background services and
        close VoicePilot cleanly.
        """

        print(
            "Closing VoicePilot..."
        )

        if self.index_observer:
            stop_index_watcher(
                self.index_observer
            )

            self.index_observer = None

        self.destroy()


def run_ui():
    app = VoicePilotApp()

    app.mainloop()


if __name__ == "__main__":
    run_ui()