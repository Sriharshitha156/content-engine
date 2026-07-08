"""
config.py
Loads API keys and model settings from .env
"""

import os
from dotenv import load_dotenv

load_dotenv()

# --- API Keys ---
# For DeepSeek: reuse the existing OPENROUTER_API_KEY env name or set DEEPSEEK_API_KEY
OPENROUTER_API_KEY = os.getenv("DEEPSEEK_API_KEY", os.getenv("OPENROUTER_API_KEY", ""))
# For video (WAN) we typically use Replicate — set REPLICATE_API_TOKEN in your .env
RUNWAY_API_KEY = os.getenv("REPLICATE_API_TOKEN", os.getenv("RUNWAY_API_KEY", ""))
# Image provider key (HuggingFace / Replicate) — keep GPT_IMAGE_API_KEY as the env name
GPT_IMAGE_API_KEY = os.getenv("GPT_IMAGE_API_KEY", os.getenv("OPENROUTER_API_KEY", ""))
# Edge TTS uses the local `edge-tts` package; no remote TTS key required by default

# --- Model settings ---
# Default to DeepSeek's API endpoint. You can keep OpenRouter if you proxy through it.
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://api.deepseek.com")
TEXT_MODEL = os.getenv("TEXT_MODEL", "deepseek-chat")

# Image generation: point at a Flux-hosting endpoint (Hugging Face inference or Replicate)
GPT_IMAGE_MODEL = os.getenv("GPT_IMAGE_MODEL", "black-forest-labs/FLUX.1")
GPT_IMAGE_BASE_URL = os.getenv("GPT_IMAGE_BASE_URL", "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1")

# Video generation: use Replicate (WAN) by default — set REPLICATE_API_TOKEN in .env
RUNWAY_BASE_URL = os.getenv("RUNWAY_BASE_URL", "https://api.replicate.com/v1")
RUNWAY_MODEL = os.getenv("RUNWAY_MODEL", "owner/wan-model")

# Edge TTS: we use the local `edge-tts` package which doesn't require an HTTP base URL
TTS_VOICE = os.getenv("TTS_VOICE", "alloy")

# --- App settings ---
MAX_CRITIC_RETRIES = 2

TONE_OPTIONS = ["playful", "premium", "eco", "clean modern"]
CHANNEL_OPTIONS = ["B2B LinkedIn", "Gen-Z TikTok", "Parents Facebook"]

STYLE_MAP = {
    "playful": "bright flat illustration",
    "premium": "photorealistic, studio lighting",
    "eco": "watercolour, natural tones",
}
DEFAULT_STYLE = "clean modern"


def check_keys():
    """Return a dict of which keys are missing, for friendly UI warnings."""
    missing = []
    if not OPENROUTER_API_KEY:
        missing.append("OPENROUTER_API_KEY")
    if not RUNWAY_API_KEY:
        missing.append("RUNWAY_API_KEY")
    # image key is optional if using public HF models, but warn if not present
    if not GPT_IMAGE_API_KEY:
        missing.append("GPT_IMAGE_API_KEY")
    return missing
