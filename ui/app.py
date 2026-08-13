import threading

import customtkinter as ctk

from main import execute_command

from context.folder_context import (
    get_current_folder,
)

from context.rename_context import (
    has_pending_rename,
)

from actions.file_actions import (
    has_pending_file_selection,
)

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


# Small pause before VoicePilot automatically
# begins listening for a follow-up response.
FOLLOW_UP_DELAY = 400


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
            "500x720"
        )

        self.minsize(
            450,
            620,
        )

        self.center_window()

        self.is_listening = False

        # Tells the UI whether the microphone
        # is listening for a normal command
        # or a response to a previous command.
        self.is_follow_up = False

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
                25,
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
                20,
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
                10,
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
        # CURRENT FOLDER
        # ------------------------------------------

        self.folder_frame = (
            ctk.CTkFrame(
                self.main_frame,
                corner_radius=12,
            )
        )

        self.folder_frame.pack(
            fill="x",
            padx=25,
            pady=(
                0,
                10,
            ),
        )

        self.folder_title = (
            ctk.CTkLabel(
                self.folder_frame,
                text="Current Folder",
                font=ctk.CTkFont(
                    size=13,
                    weight="bold",
                ),
                text_color="gray70",
            )
        )

        self.folder_title.pack(
            anchor="w",
            padx=15,
            pady=(
                12,
                5,
            ),
        )

        self.folder_label = (
            ctk.CTkLabel(
                self.folder_frame,
                text="📁 No folder selected",
                font=ctk.CTkFont(
                    size=15,
                ),
                wraplength=380,
                justify="left",
            )
        )

        self.folder_label.pack(
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

        # ------------------------------------------
        # INITIAL FOLDER DISPLAY
        # ------------------------------------------

        self.update_current_folder_display()

    # --------------------------------------------------
    # MICROPHONE BUTTON
    # --------------------------------------------------

    def handle_mic_click(self):
        """
        Start a normal command listening cycle
        when the user clicks the microphone.
        """

        self.start_listening(
            follow_up=False
        )

    # --------------------------------------------------
    # START LISTENING
    # --------------------------------------------------

    def start_listening(
        self,
        follow_up=False,
    ):
        """
        Start listening for either:

        - a new VoicePilot command
        - a follow-up response to a
          previous command
        """

        if self.is_listening:
            return

        self.is_listening = True
        self.is_follow_up = follow_up

        self.status_label.configure(
            text="● Listening..."
        )

        if follow_up:
            self.listen_label.configure(
                text="Listening for response..."
            )

            self.command_label.configure(
                text=(
                    "Listening for "
                    "your response..."
                )
            )

            # Do NOT clear the VoicePilot
            # response during a follow-up.
            #
            # The user should still be able
            # to see the question that
            # VoicePilot just asked.

        else:
            self.listen_label.configure(
                text="Listening..."
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

        self.mic_button.configure(
            state="disabled"
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

        The parser decides whether the
        transcription is:

        - a new command
        - a rename response
        - a file-selection response
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
        # EXECUTE THROUGH EXISTING
        # VOICEPILOT COMMAND ENGINE
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
    # CHECK FOLLOW-UP STATE
    # --------------------------------------------------

    def needs_follow_up(self):
        """
        Return True when VoicePilot is
        currently waiting for another
        spoken response.

        Examples:

        rename file notes
        -> waiting for new name

        open file report
        -> multiple matches found
        -> waiting for selection
        """

        if has_pending_rename():
            return True

        if has_pending_file_selection():
            return True

        return False

    # --------------------------------------------------
    # AUTOMATIC FOLLOW-UP
    # --------------------------------------------------

    def begin_follow_up(self):
        """
        Automatically start listening again
        when VoicePilot is waiting for more
        information.
        """

        if self.is_listening:
            return

        if not self.needs_follow_up():
            return

        print(
            "Waiting for follow-up response..."
        )

        self.start_listening(
            follow_up=True
        )

    # --------------------------------------------------
    # CURRENT FOLDER DISPLAY
    # --------------------------------------------------

    def update_current_folder_display(self):
        """
        Refresh the current folder shown
        inside the VoicePilot UI.
        """

        current_folder = (
            get_current_folder()
        )

        if not current_folder:
            self.folder_label.configure(
                text="📁 No folder selected"
            )

            return

        folder_name = (
            current_folder.name
        )

        if not folder_name:
            folder_name = str(
                current_folder
            )

        self.folder_label.configure(
            text=f"📁 {folder_name}"
        )

    # --------------------------------------------------
    # COMMAND COMPLETE
    # --------------------------------------------------

    def command_finished(
        self,
        result,
    ):
        self.is_listening = False
        self.is_follow_up = False

        # ------------------------------------------
        # UPDATE CURRENT FOLDER
        # ------------------------------------------

        self.update_current_folder_display()

        # ------------------------------------------
        # RESPONSE
        # ------------------------------------------

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

        # ------------------------------------------
        # EXIT
        # ------------------------------------------

        if result.get("exit"):
            self.status_label.configure(
                text="● Closing..."
            )

            self.listen_label.configure(
                text="Closing..."
            )

            self.after(
                500,
                self.close_application,
            )

            return

        # ------------------------------------------
        # FOLLOW-UP REQUIRED
        # ------------------------------------------

        if self.needs_follow_up():
            self.status_label.configure(
                text="● Waiting for response..."
            )

            self.listen_label.configure(
                text="Waiting for response..."
            )

            # Keep the manual microphone
            # disabled because VoicePilot
            # is about to listen automatically.
            self.mic_button.configure(
                state="disabled"
            )

            self.after(
                FOLLOW_UP_DELAY,
                self.begin_follow_up,
            )

            return

        # ------------------------------------------
        # NORMAL COMMAND COMPLETE
        # ------------------------------------------

        self.mic_button.configure(
            state="normal"
        )

        self.status_label.configure(
            text="● Ready"
        )

        self.listen_label.configure(
            text="Start Listening"
        )

    # --------------------------------------------------
    # NO AUDIO
    # --------------------------------------------------

    def handle_no_audio(self):
        self.is_listening = False

        # If VoicePilot was waiting for
        # additional information, don't
        # destroy the pending context.
        if self.needs_follow_up():
            self.mic_button.configure(
                state="normal"
            )

            self.command_label.configure(
                text="No response detected."
            )

            self.status_label.configure(
                text="● Waiting for response"
            )

            self.listen_label.configure(
                text="Tap to Respond"
            )

            self.response_label.configure(
                text=(
                    "I couldn't hear your response. "
                    "Tap the microphone to try again."
                )
            )

            return

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

        # Preserve pending rename/file
        # selection context so the user
        # can try answering again.
        if self.needs_follow_up():
            self.mic_button.configure(
                state="normal"
            )

            self.command_label.configure(
                text=(
                    "I couldn't understand "
                    "your response."
                )
            )

            self.response_label.configure(
                text=(
                    "Tap the microphone "
                    "and try your response again."
                )
            )

            self.status_label.configure(
                text="● Waiting for response"
            )

            self.listen_label.configure(
                text="Tap to Respond"
            )

            return

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
        height = 720

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