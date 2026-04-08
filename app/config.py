import os
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# GEMINI
# =============================================================================
GEMINI_API_KEY: str = os.environ["GEMINI_API_KEY"]
GEMINI_MODEL: str = "gemini-2.5-flash"
GEMINI_TEMPERATURE: float = 0.9
GEMINI_MAX_TOKENS: int = 3000

# =============================================================================
# GOOGLE CLOUD STORAGE
# =============================================================================
GCS_BUCKET_NAME: str = os.getenv("GCS_BUCKET_NAME", "fable-backend-3-0")

# =============================================================================
# TTS
# =============================================================================
TTS_SPEAKING_RATE: float = 0.9
TTS_PITCH: float = 0.0
TTS_EFFECTS_PROFILE: list[str] = ["small-bluetooth-speaker-class-device"]

# 🔥 SAFE LIMIT (VERY IMPORTANT)
TTS_MAX_BYTES: int = 4800

VOICE_CONFIG: dict[str, dict] = {
    "Hindi": {
        "language_code": "hi-IN",
        "name": "hi-IN-Neural2-A",  # 🔥 upgraded voice
    },
    "English": {
        "language_code": "en-US",
        "name": "en-US-Neural2-F",
    },
    "Gujarati": {
        "language_code": "gu-IN",
        "name": "gu-IN-Wavenet-A",
    },
}

VOICE_DEFAULT: dict = VOICE_CONFIG["Hindi"]

# =============================================================================
# STORY VALIDATION
# =============================================================================
STORY_MIN_WORDS: int = 200
SENTENCE_END_CHARS: tuple = ("।", ".", "!", "?")