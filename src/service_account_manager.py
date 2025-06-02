"""Service account management module for handling user service accounts."""

import json
import uuid
from pathlib import Path
from typing import Optional

import streamlit as st
from google.cloud import texttospeech
from google.oauth2 import service_account

# Directory to store service account files
SERVICE_ACCOUNTS_DIR = Path("credentials/user_service_accounts")
SERVICE_ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)


def get_user_id() -> str:
    """Get or create a unique user ID stored in cookies."""
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    return st.session_state.user_id


def get_user_service_account_path(user_id: str) -> Optional[Path]:
    """Get the path to a user's service account file if it exists."""
    account_path = SERVICE_ACCOUNTS_DIR / f"{user_id}.json"
    return account_path if account_path.exists() else None


def save_service_account(user_id: str, service_account_file) -> bool:
    """Save uploaded service account file for a user."""
    try:
        # Read and validate the service account JSON
        service_account_data = json.load(service_account_file)
        required_fields = ["type", "project_id", "private_key_id", "private_key", "client_email"]
        if not all(field in service_account_data for field in required_fields):
            return False

        # Save the service account file
        account_path = SERVICE_ACCOUNTS_DIR / f"{user_id}.json"
        with open(account_path, "w") as f:
            json.dump(service_account_data, f)
        return True
    except Exception:
        return False


def remove_service_account(user_id: str) -> bool:
    """Remove a user's service account file."""
    try:
        account_path = SERVICE_ACCOUNTS_DIR / f"{user_id}.json"
        if account_path.exists():
            account_path.unlink()
        return True
    except Exception:
        return False


def get_text_to_speech_client(user_id: str) -> Optional[texttospeech.TextToSpeechClient]:
    """Get a Text-to-Speech client using the user's service account."""
    account_path = get_user_service_account_path(user_id)
    if not account_path:
        return None

    try:
        credentials = service_account.Credentials.from_service_account_file(
            str(account_path), scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        return texttospeech.TextToSpeechClient(credentials=credentials)
    except Exception:
        return None
