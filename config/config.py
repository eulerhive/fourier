"""Configuration for audio, UI, and file paths for the Text to Speech Generator app."""

import os

# Audio configuration
AUDIO_ENCODING = "MP3"
DEFAULT_SPEED = 1.0
DEFAULT_PITCH = 0.0

# UI Configuration
PAGE_TITLE = "Text to Speech Generator"
PAGE_ICON = "🎙️"

# File paths
TEMP_DIR = "temp"
OUTPUT_DIR = "output"

# Create necessary directories
for directory in [TEMP_DIR, OUTPUT_DIR]:
    os.makedirs(directory, exist_ok=True)
