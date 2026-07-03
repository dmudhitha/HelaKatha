import sys
import time
import os
import json
from contextlib import contextmanager
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QEventLoop, QTimer, QThread
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from PyQt6.QtGui import QFontDatabase

from pynput.keyboard import Key, Listener as KeyboardListener, Controller as KeyboardController
from pynput.mouse import Listener as MouseListener

# Import local modules
from engine import TransliterationEngine, unicode_to_fm_abhaya
from ui import CandidateWindow, NotificationOSD, HelpDialog, create_status_icon, LanguageBar

@contextmanager
def suppress_stderr():
    """
    Temporarily redirects stderr to /dev/null at the system file-descriptor level.
    This suppresses PortAudio/ALSA diagnostic warnings printed during initialization.
    """
    try:
        stderr_fd = sys.stderr.fileno()
        save_fd = os.dup(stderr_fd)
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, stderr_fd)
        os.close(devnull)
        try:
            yield
        finally:
            os.dup2(save_fd, stderr_fd)
            os.close(save_fd)
    except Exception:
        yield

class VoiceDictationWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    status = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self):
        try:
            import speech_recognition as sr
        except ImportError:
            self.error.emit("Missing library: Install SpeechRecognition")
            return

        r = sr.Recognizer()
        r.pause_threshold = 0.8
        r.non_speaking_duration = 0.5

        # Instantiate microphone and open stream while suppressing ALSA C-level warnings
        try:
            with suppress_stderr():
                microphone = sr.Microphone()
                audio_context = microphone.__enter__()
        except Exception as e:
            self.error.emit("Mic Error: Verify microphone connection")
            return

        try:
            self.status.emit("Adjusting noise...")
            r.adjust_for_ambient_noise(audio_context, duration=0.5)
            
            if not self.running:
                return
                
            self.status.emit("Listening (Speak Sinhala)...")
            audio = r.listen(audio_context, timeout=4, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            self.error.emit("Timeout: No speech detected")
            return
        except Exception as e:
            self.error.emit("Mic Error: Install PyAudio or verify microphone")
            return
        finally:
            with suppress_stderr():
                try:
                    microphone.__exit__(None, None, None)
                except Exception:
                    pass

        if not self.running:
            return

        self.status.emit("Transcribing...")
        try:
            # Call Google Web Speech API with si-LK (Sinhala)
            text = r.recognize_google(audio, language="si-LK")
            if text:
                self.finished.emit(text)
            else:
                self.error.emit("No text recognized")
        except sr.UnknownValueError:
            self.error.emit("Could not understand audio")
        except sr.RequestError:
            self.error.emit("Network request failed")
        except Exception as e:
            self.error.emit(f"Error: {str(e)}")

    def stop(self):
        self.running = False

class SinglishInputController(QObject):
    # Cross-thread safe Qt Signals to communicate from background threads to GUI thread
    sig_update_ui = pyqtSignal(str, list)
    sig_hide_ui = pyqtSignal()
    sig_toggle_state = pyqtSignal(bool)
    sig_replace_text = pyqtSignal(int, str, str)
    sig_toggle_voice = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        # 1. Initialize Engine & UI Windows
        self.engine = TransliterationEngine()
        self.candidate_window = CandidateWindow()
        self.osd = NotificationOSD()
        self.help_dialog = HelpDialog()
        self.lang_bar = LanguageBar()
        
        # Load custom font settings (Unicode vs Legacy FM Abhaya)
        self.load_settings()
        
        # 2. Virtual Key Injector
        self.keyboard_controller = KeyboardController()
        
        # 3. Intercept & Buffer State
        self.buffer = ""
        self.is_enabled = True
        self.is_injecting = False
        self.ctrl_pressed = False
        self.alt_pressed = False
        self.shift_pressed = False
        self.win_pressed = False
        
        # Voice Dictation State
        self.is_dictating = False
        self.dictation_worker = None
        
        # 4. Connect Cross-Thread Signals to Local GUI Slots
        self.sig_update_ui.connect(self.handle_update_ui)
        self.sig_hide_ui.connect(self.handle_hide_ui)
        self.sig_toggle_state.connect(self.handle_toggle_state)
        self.sig_replace_text.connect(self.handle_replace_text)
        self.sig_toggle_voice.connect(self.toggle_voice_dictation)
        self.lang_bar.clicked.connect(self.toggle_mode_clicked)
        self.lang_bar.mic_clicked.connect(self.toggle_voice_dictation)
        self.help_dialog.font_settings_changed.connect(self.handle_font_settings_changed)
        self.help_dialog.shortcut_settings_changed.connect(self.handle_shortcut_settings_changed)
        
        # 5. Initialize System Tray Icon
        self.setup_tray_icon()
        
        # 6. Start Global Listeners in Background Threads
        self.start_listeners()
        
        # Show initial OSD greeting
        time.sleep(0.1) # Small delay to let Qt stabilize
        self.sig_toggle_state.emit(self.is_enabled)

    def setup_tray_icon(self):
        """
        Creates and configures the system tray icon and its context menu.
        """
        try:
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(create_status_icon(self.is_enabled))
            self.tray_icon.setToolTip("HelaKatha Input Tool")
            
            # Tray context menu
            self.tray_menu = QMenu()
            
            self.toggle_action = self.tray_menu.addAction("HelaKatha Enabled")
            self.toggle_action.setCheckable(True)
            self.toggle_action.setChecked(self.is_enabled)
            self.toggle_action.triggered.connect(self.menu_toggle_triggered)
            
            voice_action = self.tray_menu.addAction("Voice Typing (Ctrl+Alt+S)")
            voice_action.triggered.connect(self.toggle_voice_dictation)
            
            self.tray_menu.addSeparator()
            
            help_action = self.tray_menu.addAction("Typing Guide (Help)")
            help_action.triggered.connect(self.show_help_dialog)
            
            quit_action = self.tray_menu.addAction("Quit App")
            quit_action.triggered.connect(self.quit_application)
            
            self.tray_icon.setContextMenu(self.tray_menu)
            
            # Single click on icon toggles state, double click shows help
            self.tray_icon.activated.connect(self.on_tray_activated)
            self.tray_icon.show()
        except Exception as e:
            print(f"System tray initialization failed: {e}. Running without system tray.")

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger: # Single click
            self.is_enabled = not self.is_enabled
            self.buffer = ""
            self.sig_toggle_state.emit(self.is_enabled)
            self.sig_hide_ui.emit()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick: # Double click
            self.show_help_dialog()

    def menu_toggle_triggered(self):
        self.is_enabled = self.toggle_action.isChecked()
        self.buffer = ""
        self.sig_toggle_state.emit(self.is_enabled)
        self.sig_hide_ui.emit()

    def show_help_dialog(self):
        # Load currently active settings into UI fields
        self.help_dialog.load_initial_settings(
            self.font_path, self.font_family, self.is_legacy_font,
            self.shortcut_toggle, self.shortcut_voice
        )
        self.help_dialog.show()
        self.help_dialog.raise_()
        self.help_dialog.activateWindow()

    def toggle_voice_dictation(self):
        if self.is_dictating:
            self.cancel_voice_dictation()
        else:
            self.start_voice_dictation()

    def start_voice_dictation(self):
        if self.is_injecting:
            return
            
        self.is_dictating = True
        self.lang_bar.set_mic_state("listening")
        
        # Instantiate and start the worker thread
        self.dictation_worker = VoiceDictationWorker()
        self.dictation_worker.status.connect(self.handle_voice_status)
        self.dictation_worker.finished.connect(self.handle_voice_success)
        self.dictation_worker.error.connect(self.handle_voice_error)
        self.dictation_worker.start()

    def cancel_voice_dictation(self):
        if self.dictation_worker:
            self.dictation_worker.stop()
            self.dictation_worker.wait()
            self.dictation_worker = None
            
        self.is_dictating = False
        self.lang_bar.set_mic_state("idle")
        self.osd.show_dictation_message("Voice Typing", "Canceled", persistent=False)

    def handle_voice_status(self, status_text):
        if not self.is_dictating:
            return
            
        if "Listening" in status_text:
            self.lang_bar.set_mic_state("listening")
        elif "Transcribing" in status_text:
            self.lang_bar.set_mic_state("transcribing")
            
        self.osd.show_dictation_message("Voice Typing", status_text, persistent=True)

    def handle_voice_success(self, text):
        self.is_dictating = False
        self.lang_bar.set_mic_state("idle")
        self.dictation_worker = None
        
        # Inject the text directly (delete_count=0)
        self.sig_replace_text.emit(0, text, "")
        
        self.osd.show_dictation_message(
            "Voice Typing",
            f"You said: {text}",
            border_color="rgba(166, 227, 161, 150)", # soft green
            text_color="#a6e3a1",
            persistent=False
        )

    def handle_voice_error(self, error_text):
        self.is_dictating = False
        self.lang_bar.set_mic_state("idle")
        self.dictation_worker = None
        
        self.osd.show_dictation_message(
            "Voice Typing Failed",
            error_text,
            border_color="rgba(243, 139, 168, 150)", # soft red
            text_color="#f38ba8",
            persistent=False
        )

    def get_settings_path(self):
        home = os.path.expanduser("~")
        config_dir = os.path.join(home, ".gemini", "antigravity-cli")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "settings.json")

    def load_settings(self):
        self.font_path = ""
        self.font_family = ""
        self.is_legacy_font = False
        self.shortcut_toggle = "Ctrl+Space"
        self.shortcut_voice = "Ctrl+Alt+S"
        
        settings_file = self.get_settings_path()
        if os.path.exists(settings_file):
            try:
                with open(settings_file, "r") as f:
                    data = json.load(f)
                    self.font_path = data.get("font_path", "")
                    self.font_family = data.get("font_family", "")
                    self.is_legacy_font = data.get("is_legacy_font", False)
                    self.shortcut_toggle = data.get("shortcut_toggle", "Ctrl+Space")
                    self.shortcut_voice = data.get("shortcut_voice", "Ctrl+Alt+S")
            except Exception as e:
                print(f"Error loading settings.json: {e}")
                
        # Apply font settings if font_path exists
        if self.font_path and os.path.exists(self.font_path):
            font_id = QFontDatabase.addApplicationFont(self.font_path)
            if font_id != -1:
                families = QFontDatabase.applicationFontFamilies(font_id)
                if families:
                    self.font_family = families[0]
                    self.candidate_window.set_font_family(self.font_family)
                    print(f"Loaded custom font on startup: {self.font_family}")
        else:
            self.font_path = ""
            self.font_family = ""
            self.candidate_window.set_font_family("")

    def save_settings(self):
        settings_file = self.get_settings_path()
        try:
            with open(settings_file, "w") as f:
                json.dump({
                    "font_path": self.font_path,
                    "font_family": self.font_family,
                    "is_legacy_font": self.is_legacy_font,
                    "shortcut_toggle": self.shortcut_toggle,
                    "shortcut_voice": self.shortcut_voice
                }, f, indent=4)
        except Exception as e:
            print(f"Error saving settings.json: {e}")

    def handle_font_settings_changed(self, path, family, is_legacy):
        self.font_path = path
        self.font_family = family
        self.is_legacy_font = is_legacy
        
        # Apply font to CandidateWindow
        self.candidate_window.set_font_family(family)
        
        # Save settings
        self.save_settings()

    def handle_shortcut_settings_changed(self, shortcut_toggle, shortcut_voice):
        self.shortcut_toggle = shortcut_toggle
        self.shortcut_voice = shortcut_voice
        self.save_settings()

    def start_listeners(self):
        """
        Starts pynput listeners for both keyboard (intercepts typing)
        and mouse (clears buffer on click outside).
        """
        # Keyboard Listener (background thread)
        self.keyboard_listener = KeyboardListener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.keyboard_listener.start()
        
        # Mouse Listener (background thread)
        self.mouse_listener = MouseListener(
            on_click=self.on_click
        )
        self.mouse_listener.start()
        print("Background key/mouse listeners started successfully.")

    # ==========================================
    # Global Interception Logic (Background Thread)
    # ==========================================
    
    def on_press(self, key):
        if self.is_injecting:
            return

        # Track state of modifiers
        if key in (Key.ctrl_l, Key.ctrl_r, Key.ctrl):
            self.ctrl_pressed = True
            return
        if key in (Key.alt_l, Key.alt_r, Key.alt):
            self.alt_pressed = True
            return
        if key in (Key.shift_l, Key.shift_r, Key.shift):
            self.shift_pressed = True
            return
        if key in (Key.cmd_l, Key.cmd_r, Key.cmd):
            self.win_pressed = True
            return

        # Build modifier combination
        modifiers = []
        if self.ctrl_pressed:
            modifiers.append("Ctrl")
        if self.alt_pressed:
            modifiers.append("Alt")
        if self.shift_pressed:
            modifiers.append("Shift")
        if self.win_pressed:
            modifiers.append("Meta")

        def get_key_name(k):
            if hasattr(k, 'char') and k.char is not None:
                return k.char.upper()
            if k == Key.space:
                return "Space"
            if k == Key.enter:
                return "Enter"
            if k == Key.tab:
                return "Tab"
            if k == Key.esc:
                return "Esc"
            key_str = str(k)
            if key_str.startswith("Key."):
                return key_str[4:].capitalize()
            return None

        key_name = get_key_name(key)
        if key_name and key_name not in ("Ctrl", "Alt", "Shift", "Cmd", "Meta"):
            combo = "+".join(modifiers + [key_name])
            combo_lower = combo.lower()
            
            # Check for keyboard shortcuts
            if combo_lower == self.shortcut_toggle.lower():
                self.is_enabled = not self.is_enabled
                self.buffer = ""
                self.sig_toggle_state.emit(self.is_enabled)
                self.sig_hide_ui.emit()
                return
            
            if combo_lower == self.shortcut_voice.lower():
                self.sig_toggle_voice.emit()
                return

        if not self.is_enabled:
            return

        # Handle Backspace
        if key == Key.backspace:
            if len(self.buffer) > 0:
                self.buffer = self.buffer[:-1]
                if self.buffer:
                    candidates = self.engine.get_candidates(self.buffer)
                    self.sig_update_ui.emit(self.buffer, candidates)
                else:
                    self.sig_hide_ui.emit()
            else:
                self.sig_hide_ui.emit()
            return

        # Handle Escape (cancel/hide box but keep typed English text, or cancel voice dictation)
        if key == Key.esc:
            if self.is_dictating:
                self.sig_toggle_voice.emit()
                return
            if self.buffer:
                self.buffer = ""
                self.sig_hide_ui.emit()
            return

        # Process standard characters
        try:
            char = None
            if hasattr(key, 'char') and key.char is not None:
                char = key.char
            
            if char:
                # Buffer standard letters, numbers, and key symbols in Singlish
                if char.isalnum() or char in (')', '/', '\\', '-'):
                    # If buffer is empty, do not buffer numeric inputs
                    if not self.buffer and char.isdigit():
                        return
                    
                    # Direct number key selection (1-5) when buffer is active
                    if self.buffer and char in ('1', '2', '3', '4', '5'):
                        index = int(char) - 1
                        candidates = self.engine.get_candidates(self.buffer)
                        if index < len(candidates):
                            selected_word = candidates[index]
                            # User typed the number, so delete buffer + the number typed (buffer_len + 1)
                            delete_count = len(self.buffer) + 1
                            self.sig_replace_text.emit(delete_count, selected_word, char)
                        return

                    self.buffer += char
                    candidates = self.engine.get_candidates(self.buffer)
                    self.sig_update_ui.emit(self.buffer, candidates)
            
            # Handle Space or Enter selection
            elif key in (Key.space, Key.enter):
                if self.buffer:
                    candidates = self.engine.get_candidates(self.buffer)
                    if candidates:
                        selected_word = candidates[0]
                        # Space/Enter is typed in editor, so delete buffer + space/enter (buffer_len + 1)
                        delete_count = len(self.buffer) + 1
                        extra_char = ' ' if key == Key.space else '\n'
                        self.sig_replace_text.emit(delete_count, selected_word, extra_char)

        except Exception as e:
            print(f"Error in keyboard listener: {e}")

    def on_release(self, key):
        if key in (Key.ctrl_l, Key.ctrl_r, Key.ctrl):
            self.ctrl_pressed = False
        if key in (Key.alt_l, Key.alt_r, Key.alt):
            self.alt_pressed = False
        if key in (Key.shift_l, Key.shift_r, Key.shift):
            self.shift_pressed = False
        if key in (Key.cmd_l, Key.cmd_r, Key.cmd):
            self.win_pressed = False

    def on_click(self, x, y, button, pressed):
        """
        If the user clicks the mouse anywhere on the screen, clear the buffer and hide UI.
        This handles shifting cursor focus to another window or text region.
        """
        if pressed and not self.is_injecting:
            if self.buffer:
                self.buffer = ""
                self.sig_hide_ui.emit()

    # ==========================================
    # Slot Handlers (GUI Thread Execution)
    # ==========================================

    def handle_update_ui(self, buffer_text, candidates):
        display_candidates = []
        if self.is_legacy_font:
            for c in candidates:
                if c != buffer_text:
                    display_candidates.append(unicode_to_fm_abhaya(c))
                else:
                    display_candidates.append(c)
        else:
            display_candidates = candidates
            
        self.candidate_window.update_candidates(buffer_text, display_candidates)

    def handle_hide_ui(self):
        self.candidate_window.hide()

    def handle_toggle_state(self, enabled):
        self.osd.show_message(enabled)
        self.lang_bar.set_mode(enabled)
        # Update tray icon and toggle status checkmark
        try:
            self.tray_icon.setIcon(create_status_icon(enabled))
            self.toggle_action.setChecked(enabled)
        except AttributeError:
            pass

    def toggle_mode_clicked(self):
        self.is_enabled = not self.is_enabled
        self.buffer = ""
        self.sig_toggle_state.emit(self.is_enabled)
        self.sig_hide_ui.emit()

    def handle_replace_text(self, delete_count, selected_word, extra_char):
        """
        Executes virtual key injection in the GUI thread.
        Uses clipboard copy-paste (via Shift+Insert) to bypass keyboard layout mapping issues,
        falling back to direct typing if clipboard method fails.
        """
        self.is_injecting = True
        
        # 1. Delete typed English text and trigger key
        for _ in range(delete_count):
            self.keyboard_controller.press(Key.backspace)
            self.keyboard_controller.release(Key.backspace)
            time.sleep(0.003) # Brief pause to let the text clear

        # 2. Paste Sinhala Unicode text via Clipboard
        try:
            clipboard = QApplication.clipboard()
            old_text = clipboard.text() # Save original clipboard content
            
            paste_word = unicode_to_fm_abhaya(selected_word) if self.is_legacy_font else selected_word
            clipboard.setText(paste_word + " ")
            
            # Send Shift+Insert to paste (universally supported in Linux editors and terminals)
            with self.keyboard_controller.pressed(Key.shift):
                self.keyboard_controller.press(Key.insert)
                self.keyboard_controller.release(Key.insert)
                
            # Wait 100ms for the target application to process the paste event.
            # We must use a local QEventLoop instead of time.sleep() so that the main
            # GUI thread continues running and processing X11 clipboard requests from
            # the target application. This prevents "no data available" transfer errors.
            loop = QEventLoop()
            QTimer.singleShot(100, loop.quit)
            loop.exec()
            
            # Restore original clipboard (or clear it if it was empty)
            if old_text:
                clipboard.setText(old_text)
            else:
                clipboard.clear()
        except Exception as paste_err:
            print(f"Clipboard paste injection failed: {paste_err}. Falling back to direct typing.")
            self.keyboard_controller.type(selected_word)
        
        # 3. Clean local states
        self.buffer = ""
        self.candidate_window.hide()
        
        self.is_injecting = False


    def quit_application(self):
        # Stop background listeners cleanly
        self.keyboard_listener.stop()
        self.mouse_listener.stop()
        if hasattr(self, 'dictation_worker') and self.dictation_worker:
            self.dictation_worker.stop()
            self.dictation_worker.wait()
        self.lang_bar.close()
        QApplication.instance().quit()


def main():
    # Force X11 backend for PyQt on systems that might attempt Wayland natively,
    # as global key grabbing and absolute window moves are fully robust on X11/Xwayland.
    # Note: On Wayland, this forces Xwayland mode which behaves correctly.
    # To bypass errors, you can check:
    import os
    if "WAYLAND_DISPLAY" in os.environ and "QT_QPA_PLATFORM" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "xcb"
        
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) # Prevents app exiting when candidate box hides
    
    controller = SinglishInputController()
    
    # Run the Qt application loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
