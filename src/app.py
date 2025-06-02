"""A Streamlit application for generating speech from text using Google Cloud Text-to-Speech API.

This module provides a web interface for converting text to speech with various
language and voice options. It allows users to:
- Input text for conversion
- Select from multiple languages and voices
- Adjust speech speed
- Generate and download MP3 audio files
- Manage their own service account credentials
"""

import base64
import logging
import os
import tempfile
import time
from functools import lru_cache
from typing import Dict, List, Optional

import dotenv
import streamlit as st
from google.api_core import exceptions
from google.cloud import texttospeech

from config import DEFAULT_LANGUAGE, DEFAULT_VOICE, LANGUAGE_NAMES
from service_account_manager import get_text_to_speech_client, get_user_id, remove_service_account, save_service_account

# Load environment variables
dotenv.load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Constants
MAX_TEXT_LENGTH = int(os.getenv("MAX_TEXT_LENGTH", "5000"))
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))  # seconds

# Set page config with responsive layout
st.set_page_config(
    page_title="Fourier - Text to Speech by EulerHive",
    page_icon="src/assets/favicon.ico",  # Changed to .ico for better compatibility
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/EulerHive/Fourier",
        "Report a bug": "https://github.com/EulerHive/Fourier/issues",
        "About": "Fourier - Text to Speech Generator by EulerHive",
    },
)

# Add custom CSS for better mobile responsiveness and company branding
st.markdown(
    """
    <style>
        :root {
            --primary-color: #512FEB;
            --primary-light: #6B4AFF;
            --bg-dark: #121212;
            --bg-card: #1E1E1E;
            --text-primary: #FFFFFF;
            --text-secondary: #B3B3B3;
            --border-neutral: #232323;
        }
        .stApp {
            background-color: var(--bg-dark);
            color: var(--text-primary);
        }
        .company-header {
            display: flex;
            align-items: center;
            margin-bottom: 2rem;
            padding: 1.5rem;
            background: var(--bg-card);
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            border: 1px solid var(--border-neutral);
        }
        .company-logo {
            width: 150px !important;
            height: auto !important;
            object-fit: contain !important;
            margin-right: 2rem;
        }
        .company-title {
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--text-primary);
            margin: 0;
            font-family: 'Helvetica Neue', Arial, sans-serif;
        }
        .company-subtitle {
            font-size: 1.1rem;
            color: var(--text-secondary);
            margin: 0.5rem 0 0 0;
            line-height: 1.5;
        }
        /* Button styling */
        .stButton button {
            background: var(--primary-color);
            color: var(--text-primary);
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            transition: all 0.3s ease;
            font-weight: 600;
        }
        .stButton button:hover {
            background: var(--primary-light);
            box-shadow: 0 4px 8px rgba(81, 47, 235, 0.2);
        }
        /* Sidebar button (remove service account) */
        .sidebar-content .stButton button {
            background: var(--bg-card);
            color: var(--primary-color);
            border: 1px solid var(--primary-color);
        }
        .sidebar-content .stButton button:hover {
            background: var(--primary-color);
            color: var(--text-primary);
        }
        /* Input fields styling */
        .stTextArea textarea {
            background-color: var(--bg-card) !important;
            color: var(--text-primary) !important;
            border: 1px solid var(--border-neutral) !important;
            transition: border 0.2s;
        }
        .stTextArea textarea:focus {
            border: 1.5px solid var(--primary-color) !important;
        }
        .stSelectbox {
            background-color: var(--bg-card) !important;
        }
        .stSelectbox div[data-baseweb="select"] {
            background-color: var(--bg-card) !important;
            border: 1px solid var(--border-neutral) !important;
            transition: border 0.2s;
        }
        .stSelectbox div[data-baseweb="select"]:focus-within {
            border: 1.5px solid var(--primary-color) !important;
        }
        .stSelectbox div[data-baseweb="select"] span {
            color: var(--text-primary) !important;
        }
        /* Slider styling */
        .stSlider {
            background-color: transparent !important;
        }
        .stSlider div[data-baseweb="slider"] {
            background-color: transparent !important;
        }
        .stSlider .rc-slider-track {
            background-color: var(--primary-color) !important;
        }
        .stSlider .rc-slider-rail {
            background-color: var(--border-neutral) !important;
        }
        .stSlider .rc-slider-handle {
            background-color: var(--primary-color) !important;
            border: 2px solid var(--primary-light) !important;
        }
        .stSlider .rc-slider-handle:active {
            border: 2px solid var(--primary-color) !important;
        }
        .stSlider .rc-slider-dot {
            background: var(--bg-card) !important;
            border: 1px solid var(--border-neutral) !important;
        }
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: var(--bg-card) !important;
        }
        [data-testid="stSidebar"] .sidebar-content {
            background-color: var(--bg-card) !important;
        }
        /* Mobile responsiveness */
        @media (max-width: 768px) {
            .stTextArea textarea {
                font-size: 16px !important;
            }
            .stButton button {
                width: 100%;
            }
            .stSelectbox {
                width: 100%;
            }
            .stSlider {
                width: 100%;
            }
            [data-testid="stSidebar"] {
                width: 100% !important;
                position: relative !important;
            }
            .main .block-container.no-service-account {
                display: none;
            }
            .company-header {
                flex-direction: column;
                text-align: center;
                padding: 1rem;
            }
            .company-logo {
                margin-right: 0;
                margin-bottom: 1rem;
            }
            .company-title {
                font-size: 2rem;
            }
            .company-subtitle {
                font-size: 1rem;
            }
        }
        .company-eulerhive {
            color: var(--primary-color);
            font-weight: bold;
            letter-spacing: 1px;
        }
        .company-details-accent {
            border-left: 4px solid var(--primary-color);
            padding-left: 1.2rem;
            background: linear-gradient(90deg, rgba(81,47,235,0.18) 0%, var(--bg-card) 100%);
            border-top-left-radius: 8px;
            border-bottom-left-radius: 8px;
        }
        .company-website-link {
            color: var(--primary-color);
            font-weight: 500;
            text-decoration: none;
            transition: color 0.2s;
            display: inline-block;
            margin-top: 0.5rem;
        }
        .company-website-link:hover {
            color: var(--primary-light);
            text-decoration: underline;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Add security headers
st.markdown(
    """
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';">
    <meta http-equiv="X-Content-Type-Options" content="nosniff">
    <meta http-equiv="X-Frame-Options" content="DENY">
    <meta http-equiv="X-XSS-Protection" content="1; mode=block">
    """,  # noqa
    unsafe_allow_html=True,
)


# Display company logo and title
def display_company_header():
    """Display the company logo and title in the header."""
    # Read and encode the logo file
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
    try:
        with open(logo_path, "rb") as f:
            logo_bytes = f.read()
            logo_base64 = base64.b64encode(logo_bytes).decode()
    except Exception as e:
        logger.error(f"Error loading logo: {str(e)}")
        logo_base64 = None

    st.markdown(
        f"""
        <div class="company-header">
            {f'<img src="data:image/png;base64,{logo_base64}" alt="EulerHive Logo" class="company-logo">' if logo_base64 else ''}
            <div class="company-details-accent">
                <h1 class="company-title">Fourier</h1>
                <p class="company-subtitle">Advanced Text-to-Speech powered by <span class="company-eulerhive">EulerHive</span>.<br>Transform your text into natural-sounding speech with our state-of-the-art technology. Featuring multi-language support, voice customization, and enterprise-grade security.</p>
                <a href="https://eulerhive.com" class="company-website-link" target="_blank">Visit EulerHive &rarr;</a>
            </div>
        </div>
        """,  # noqa
        unsafe_allow_html=True,
    )


@lru_cache(maxsize=128)
def get_voices(client) -> List[Dict]:
    """Get available voices from Google Cloud TTS with caching."""
    try:
        response = client.list_voices()
        voices = []
        for voice in response.voices:
            for language_code in voice.language_codes:
                voices.append(
                    {
                        "name": voice.name,
                        "language_code": language_code,
                        "gender": texttospeech.SsmlVoiceGender(voice.ssml_gender).name,
                    }
                )
        return voices
    except exceptions.GoogleAPIError as e:
        logger.error(f"Error fetching voices: {str(e)}")
        st.error("Failed to fetch available voices. Please try again later.")
        return []


def check_rate_limit(user_id: str) -> bool:
    """Check if user has exceeded rate limit."""
    if "rate_limit" not in st.session_state:
        st.session_state.rate_limit = {"count": 0, "window_start": time.time()}

    current_time = time.time()
    window_start = st.session_state.rate_limit["window_start"]

    if current_time - window_start > RATE_LIMIT_WINDOW:
        st.session_state.rate_limit = {"count": 0, "window_start": current_time}

    if st.session_state.rate_limit["count"] >= RATE_LIMIT_REQUESTS:
        return False

    st.session_state.rate_limit["count"] += 1
    return True


def generate_speech(client, text: str, voice_name: str, language_code: str, speed: float) -> Optional[bytes]:
    """Generate speech from text using Google Cloud TTS with error handling."""
    try:
        if len(text) > MAX_TEXT_LENGTH:
            raise ValueError(f"Text length exceeds maximum limit of {MAX_TEXT_LENGTH} characters")

        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
        )
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=speed)

        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        return response.audio_content
    except exceptions.GoogleAPIError as e:
        logger.error(f"Google API Error: {str(e)}")
        st.error("Failed to generate speech. Please check your service account credentials.")
        return None
    except ValueError as e:
        logger.error(f"Validation Error: {str(e)}")
        st.error(str(e))
        return None
    except Exception as e:
        logger.error(f"Unexpected Error: {str(e)}")
        st.error("An unexpected error occurred. Please try again later.")
        return None


def parse_voice_name(voice_name: str) -> Optional[Dict]:
    """Parse voice name into components with error handling."""
    try:
        parts = voice_name.split("-")
        if len(parts) >= 4:
            return {
                "language": parts[0],
                "country": parts[1],
                "audio_type": parts[2],
                "name": "-".join(parts[3:]),
            }
    except Exception as e:
        logger.error(f"Error parsing voice name: {str(e)}")
    return None


def format_voice_display(voice: Dict) -> str:
    """Format voice for display with error handling."""
    parsed = parse_voice_name(voice["name"])
    if parsed:
        return f"{parsed['language']}-{parsed['country']}-{parsed['audio_type']}-{parsed['name']}"
    return voice["name"]


def main():
    """Run the Streamlit Text to Speech Generator app."""
    try:
        # Display company header
        display_company_header()

        # Get user ID and initialize service account management
        user_id = get_user_id()
        client = get_text_to_speech_client(user_id)

        # Initialize history in session state if not exists
        if "history" not in st.session_state:
            st.session_state.history = []

        # Service Account Management Section
        st.sidebar.title("🔑 Service Account Setup")

        if client is None:
            st.sidebar.markdown("### First Time Setup")
            st.sidebar.markdown(
                "To use this application, you need to upload your Google Cloud service account JSON file."
            )
            st.sidebar.markdown("1. Go to Google Cloud Console")
            st.sidebar.markdown("2. Create a service account with Text-to-Speech API access")
            st.sidebar.markdown("3. Download the JSON key file")
            st.sidebar.markdown("4. Upload it here:")

            uploaded_file = st.sidebar.file_uploader("Upload Service Account JSON", type=["json"])
            if uploaded_file is not None:
                if save_service_account(user_id, uploaded_file):
                    st.sidebar.success("✅ Service account uploaded successfully!")
                    st.rerun()
                else:
                    st.sidebar.error("❌ Invalid service account file. Please try again.")
        else:
            st.sidebar.success("✅ Service account is configured!")
            if st.sidebar.button("Remove Service Account"):
                if remove_service_account(user_id):
                    st.sidebar.success("Service account removed successfully!")
                    st.rerun()
                else:
                    st.sidebar.error("Failed to remove service account.")

        if client is None:
            st.markdown('<div class="no-service-account">', unsafe_allow_html=True)
            st.warning("Please upload your service account JSON file in the sidebar to use the application.")
            st.markdown("</div>", unsafe_allow_html=True)
            return

        # Text input with mobile-friendly height and character limit
        text = st.text_area("Enter text to convert to speech:", height=100, max_chars=MAX_TEXT_LENGTH)

        # Get available voices with caching
        voices = get_voices(client)

        # Create responsive layout
        languages = sorted(list(set(voice["language_code"] for voice in voices)))
        language_options = {LANGUAGE_NAMES.get(code, code): code for code in languages}

        with st.container():
            selected_language_name = st.selectbox(
                "Select Language:",
                list(language_options.keys()),
                index=list(language_options.keys()).index(LANGUAGE_NAMES[DEFAULT_LANGUAGE]),
            )
            selected_language = language_options[selected_language_name]

            available_voices = [v for v in voices if v["language_code"] == selected_language]
            voice_names = [format_voice_display(v) for v in available_voices]
            default_voice_index = next((i for i, v in enumerate(voice_names) if DEFAULT_VOICE in v), 0)
            selected_voice = st.selectbox("Select Voice:", voice_names, index=default_voice_index)
            selected_voice_name = available_voices[voice_names.index(selected_voice)]["name"]

            speed = st.slider("Speed", 0.25, 4.0, 1.0, 0.25)

        if st.button("Generate Speech", use_container_width=True):
            if not text:
                st.warning("Please enter some text to convert to speech.")
                return

            if not check_rate_limit(user_id):
                st.error(f"Rate limit exceeded. Please wait {RATE_LIMIT_WINDOW} seconds before trying again.")
                return

            with st.spinner("Generating speech..."):
                audio_content = generate_speech(client, text, selected_voice_name, selected_language, speed)

                if audio_content:
                    # Add to history
                    history_entry = {
                        "text": text,
                        "language": selected_language_name,
                        "voice": selected_voice,
                        "speed": speed,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "audio_content": audio_content,
                    }
                    st.session_state.history.insert(0, history_entry)  # Add to beginning of list

                    # Create a temporary file to store the audio
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                        temp_file.write(audio_content)
                        temp_file_path = temp_file.name

                    try:
                        # Display audio player
                        st.audio(temp_file_path)

                        # Download button with full width on mobile
                        st.download_button(
                            label="Download Audio",
                            data=audio_content,
                            file_name="generated_speech.mp3",
                            mime="audio/mp3",
                            use_container_width=True,
                        )
                    finally:
                        # Clean up temporary file
                        try:
                            os.unlink(temp_file_path)
                        except Exception as e:
                            logger.error(f"Error cleaning up temporary file: {str(e)}")

        # Display History Section
        if st.session_state.history:
            st.markdown("---")
            st.markdown("### 📜 Generation History")

            for idx, entry in enumerate(st.session_state.history):
                with st.expander(f"{entry['timestamp']} - {entry['language']} - {entry['voice']}"):
                    st.text_area("Text", entry["text"], height=100, key=f"history_text_{idx}", disabled=True)
                    st.write(f"Speed: {entry['speed']}x")

                    # Create a temporary file for the audio
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                        temp_file.write(entry["audio_content"])
                        temp_file_path = temp_file.name

                    try:
                        st.audio(temp_file_path)
                        st.download_button(
                            label="Download Audio",
                            data=entry["audio_content"],
                            file_name=f"generated_speech_{idx}.mp3",
                            mime="audio/mp3",
                            key=f"history_download_{idx}",
                        )
                    finally:
                        try:
                            os.unlink(temp_file_path)
                        except Exception as e:
                            logger.error(f"Error cleaning up temporary file: {str(e)}")

                    if st.button("Delete Entry", key=f"delete_{idx}"):
                        st.session_state.history.pop(idx)
                        st.rerun()

    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        st.error("An unexpected error occurred. Please try again later.")


if __name__ == "__main__":
    main()
