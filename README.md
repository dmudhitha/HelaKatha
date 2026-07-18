# HelaKatha (Singlish to Sinhala Input Tool)

A complete, production-ready desktop input method tool for Linux distributions and Windows (written in Python 3 using PyQt6 and `pynput`). The application functions exactly like the "Google Singlish Input Tool"—it captures phonetic Singlish keyboard input globally, matches syllables against phonetic transliteration rules and autocomplete dictionaries, displays an elegant candidate list near the cursor, and injects the selected Sinhala script back into the active application.

HelaKatha also features a high-accuracy, real-time **Speech-to-Text (Voice Typing)** engine that allows you to speak in Sinhala or English and automatically dictates the text directly into your editor, as well as text macro expanders, auto-learning dictionaries, and spelling grammar correction.

---

## 1. Key Features

### 🌟 Premium Core Features
*   **Focus-Stealing & Caret Fix:** Uses `Qt.WindowType.X11BypassWindowManagerHint` to ensure that displaying floating candidate windows does not steal focus from your active text editor.
*   **Layout-Independent Injection:** Uses robust clipboard paste injection (`Shift+Insert` on Linux / `Ctrl+V` on Windows) to prevent collision with system layout managers, falling back to direct typing if clipboard access is restricted.
*   **Floating Shadows & Smooth Animations:** Floating widgets feature modern drop shadows for a premium 3D look. The Candidate suggestion window slides up smoothly when opening and moves between cursor tracking points with soft transitions.

### 🧠 Smart Typing & Grammar
*   **Custom User Dictionary & Auto-Learning:** Moniters your selected candidates and auto-saves your typing history to `user_dict.json`. Highly frequent words are dynamically prioritized and sorted to the top of candidates.
*   **Context-Aware Sentence Prediction (N-Gram Engine):** Learns bigrams (word pairings) on-the-fly. Committing a word displays next-word suggestions immediately, before you type a character.
*   **Text Macros & Expansion with Dynamic Variables:** Map shortcuts to long expansions (e.g. `hk = හෙළකත`). Support placeholder variables like `[date]` (inserts date), `[time]` (inserts time), and `[clip]` (inserts clipboard text).
*   **Spelling Auto-Correction:** Suggests grammatically correct forms if phonetic typos are made (such as confusing dental vs cerebral keys: e.g. `කරුනා` -> `කරුණා`).
*   **Emoji Prefix `:` Search:** Type `:` to see popular emojis, or type a query (e.g. `:smi`, `:hea`, `:lk`) to select and insert emojis directly from the keyboard candidate box.

### 🎙️ Speech & Visuals
*   **Bilingual Voice Typing:** Automatically switches voice typing languages (`si-LK` for Sinhala / `en-US` for English) based on your active keyboard mode.
*   **Vosk Local Offline Recognition:** Toggle private offline speech recognition using local Vosk acoustic models placed in `~/.gemini/antigravity-cli/vosk-model/`.
*   **Smart Spoken Punctuation:** Automatically formats spacing, casing, and replaces spoken punctuation keywords (like `"කොමාව"` -> `,`, `"තිත"` -> `.`).
*   **Audio Waveform Visualization:** Microphone audio is analyzed inside background workers using PyAudio. Live RMS volume levels stream to the OSD container to draw a dynamic, symmetric waveform visualizer during recording.
*   **Light Theme Switcher:** Toggle a check box in Settings to instantly shift the layout and theme of all screens to a clean, high-contrast Catppuccin Latte styling.

---

## 2. Project Directory Structure

```text
singlish-input-tool/
├── README.md          # Setup guide and instructions
├── engine.py          # Phonetic Singlish parser, macros, corrections, and bigrams
├── ui.py              # Dark/Light PyQt6 screens, waveform canvas, and guide dialog
├── main.py            # Main application loop, clipboard caching, and key listeners
├── ibus_engine.py     # Native Linux IBus layout daemon script
└── windows/           # Windows port directory with setup launchers
```

---

## 3. Native Linux Input Framework (IBus Engine)

For advanced Linux users who prefer system keyboard layout integration instead of running pynput overlays, HelaKatha provides a native IBus input engine daemon:
1.  Verify python GLib and IBus bindings are installed (`sudo apt install python3-gi`).
2.  The script **`ibus_engine.py`** registers `helakatha-singlish` with the native layout manager daemon, processing events at the OS keyboard layout level and committing text via native layout API text-commits.

---

## 4. Setup & Running Instructions

### Linux Installation
1.  **Automated Install:**
    ```bash
    cd singlish-input-tool
    chmod +x install.sh
    ./install.sh
    ```
    *This configures dependencies, sets up a virtual environment, generates desktop files, and configures system startup.*

2.  **Manual Start:**
    ```bash
    python3 main.py
    ```

### Windows Installation
1.  Navigate to the `windows` folder.
2.  Run `install.bat` to download dependencies.
3.  Double-click `run.bat` to launch, or compile a standalone executable using the `build_installer.bat` installer script.

---

## 5. How to Use

*   **Toggle State:** Press **`Ctrl + Space`** (customizable) or click `සි`/`EN` in the floating language bar.
*   **Select Candidates:** Press `Space` / `Enter` for candidate #1, or press `1-5` for specific candidates.
*   **Trigger Voice Typing:** Press **`Ctrl + Alt + S`** (customizable) or click the `🎙️` icon. Speak when the screen displays **`Listening`** and shows the waveform canvas animating.
*   **Dismiss overlays:** Press `Esc`.
*   **Macros & Light Mode:** Right-click the system tray icon, click **Typing Guide (Help)**, and navigate the settings tabs. Write macros in the format `shortcut = expansion` under the **Text Macros** tab.
