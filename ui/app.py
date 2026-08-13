import threading

import customtkinter as ctk

from speech.recorder import record_audio


# --------------------------------------------------
# APPEARANCE
# --------------------------------------------------

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class VoicePilotApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ------------------------------------------
        # WINDOW
        # ------------------------------------------

        self.title("VoicePilot")
        self.geometry("500x650")

        self.minsize(
            450,
            550,
        )

        self.center_window()

        # Prevent multiple recordings
        # from starting at the same time.
        self.is_listening = False

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

        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="VoicePilot",
            font=ctk.CTkFont(
                size=30,
                weight="bold",
            ),
        )

        self.title_label.pack(
            pady=(
                35,
                5,
            )
        )

        # ------------------------------------------
        # SUBTITLE
        # ------------------------------------------

        self.subtitle_label = ctk.CTkLabel(
            self.main_frame,
            text="Your desktop voice assistant",
            font=ctk.CTkFont(
                size=14,
            ),
            text_color="gray70",
        )

        self.subtitle_label.pack(
            pady=(
                0,
                40,
            )
        )

        # ------------------------------------------
        # MICROPHONE AREA
        # ------------------------------------------

        self.mic_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent",
        )

        self.mic_frame.pack(
            fill="both",
            expand=True,
        )

        self.mic_button = ctk.CTkButton(
            self.mic_frame,
            text="🎤",
            width=130,
            height=130,
            corner_radius=65,
            font=ctk.CTkFont(
                size=48,
            ),
            command=self.handle_mic_click,
        )

        self.mic_button.place(
            relx=0.5,
            rely=0.42,
            anchor="center",
        )

        # ------------------------------------------
        # BUTTON LABEL
        # ------------------------------------------

        self.listen_label = ctk.CTkLabel(
            self.mic_frame,
            text="Start Listening",
            font=ctk.CTkFont(
                size=18,
                weight="bold",
            ),
        )

        self.listen_label.place(
            relx=0.5,
            rely=0.62,
            anchor="center",
        )

        # ------------------------------------------
        # STATUS
        # ------------------------------------------

        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="● Ready",
            font=ctk.CTkFont(
                size=14,
            ),
        )

        self.status_label.pack(
            pady=(
                10,
                25,
            )
        )

    def handle_mic_click(self):
        """
        Start recording when the user
        clicks the microphone button.
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

        # Run recording outside the UI thread
        # so the application window does not freeze.
        recording_thread = threading.Thread(
            target=self.listen_for_audio,
            daemon=True,
        )

        recording_thread.start()

    def listen_for_audio(self):
        """
        Record audio using the existing
        VoicePilot recorder.
        """

        audio_path = record_audio()

        # UI updates should be scheduled
        # back onto the Tkinter main thread.
        self.after(
            0,
            self.recording_finished,
            audio_path,
        )

    def recording_finished(
        self,
        audio_path,
    ):
        """
        Handle the result after
        recording finishes.
        """

        self.is_listening = False

        self.mic_button.configure(
            state="normal"
        )

        if audio_path:
            print(
                f"Audio recorded: "
                f"{audio_path}"
            )

            self.status_label.configure(
                text="● Ready"
            )

            self.listen_label.configure(
                text="Start Listening"
            )

        else:
            print(
                "No speech was recorded."
            )

            self.status_label.configure(
                text="● No speech detected"
            )

            self.listen_label.configure(
                text="Try Again"
            )

    def center_window(self):
        """
        Center the VoicePilot window
        on the screen.
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


def run_ui():
    app = VoicePilotApp()

    app.mainloop()


if __name__ == "__main__":
    run_ui()