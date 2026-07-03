#!/bin/bash
# Singlish Input Tool Installer for all Linux Distributions
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

echo "=== Singlish Input Tool Installer ==="
echo "Detecting package manager and installing system dependencies..."

if [ -x "$(command -v apt-get)" ]; then
    echo "Detected Debian/Ubuntu-based system."
    sudo apt-get update
    sudo apt-get install -y python3-pip python3-venv xclip xsel portaudio19-dev python3-pyaudio
elif [ -x "$(command -v dnf)" ]; then
    echo "Detected Fedora/RHEL-based system."
    sudo dnf install -y python3-pip python3-virtualenv xclip xsel portaudio-devel python3-pyaudio
elif [ -x "$(command -v pacman)" ]; then
    echo "Detected Arch-based system."
    sudo pacman -S --noconfirm python-pip xclip xsel portaudio python-pyaudio
else
    echo "WARNING: Could not automatically install system dependencies (xclip, xsel, python3-venv, portaudio)."
    echo "Please ensure you have python3-venv, pip, xclip, xsel, and portaudio installed manually."
fi

echo "Creating python virtual environment in .venv..."
python3 -m venv "$DIR/.venv"

echo "Installing python dependencies (PyQt6, pynput, SpeechRecognition)..."
"$DIR/.venv/bin/pip" install --upgrade pip
"$DIR/.venv/bin/pip" install PyQt6 pynput SpeechRecognition

echo "Attempting to install PyAudio for voice typing..."
"$DIR/.venv/bin/pip" install pyaudio || echo "WARNING: PyAudio installation failed. Voice typing will require manual installation of pyaudio."

echo "Making scripts executable..."
chmod +x "$DIR/run.sh"

echo "Creating desktop launcher shortcut..."
LAUNCHER_DIR="$HOME/.local/share/applications"
mkdir -p "$LAUNCHER_DIR"

cat <<EOF > "$LAUNCHER_DIR/helakatha.desktop"
[Desktop Entry]
Type=Application
Name=HelaKatha
Comment=HelaKatha - Singlish to Sinhala Input Tool
Exec=$DIR/run.sh
Icon=input-keyboard
Terminal=false
Categories=Utility;InputMethod;
StartupNotify=false
EOF

chmod +x "$LAUNCHER_DIR/helakatha.desktop"

# Add to system autostart
AUTOSTART_DIR="$HOME/.config/autostart"
mkdir -p "$AUTOSTART_DIR"
cp "$LAUNCHER_DIR/helakatha.desktop" "$AUTOSTART_DIR/"

echo "=============================================="
echo "Installation complete!"
echo "You can search for 'HelaKatha' in your desktop application launcher to start it."
echo "It has also been added to your startup applications to run automatically on boot."
echo "=============================================="
