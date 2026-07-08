"""
voiceover.py
Pro Addition 2 - Voiceover Generation.
Rewrites the blog intro into a TTS-friendly script, then generates audio.
"""

import os
import tempfile
import asyncio
import requests
import config

try:
    import edge_tts
except Exception:
    edge_tts = None

SCRIPT_ADAPTER_SYSTEM = """Rewrite this blog intro as a voiceover script.
- Add commas for breath pauses, ellipses for dramatic pauses.
- Short sentences (max 15 words each).
- Remove visual references. Output text only, nothing else."""


def adapt_script(blog_intro):
    """Calls OpenRouter to turn the blog intro into a TTS-friendly script."""
    if not config.OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set. Add it to your .env file.")

    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.TEXT_MODEL,
        "messages": [
            {"role": "system", "content": SCRIPT_ADAPTER_SYSTEM},
            {"role": "user", "content": blog_intro},
        ],
        "max_tokens": 400,
    }

    resp = requests.post(
        f"{config.OPENROUTER_BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def generate_voiceover(blog_intro):
    """
    Adapts the blog intro into a script, then calls a TTS provider
    (OpenAI-compatible /audio/speech endpoint) and returns raw MP3 bytes.
    """
    # Use the local edge-tts package to synthesise voiceovers.
    if edge_tts is None:
        raise RuntimeError("edge-tts is not installed. Add it to requirements.txt and pip install it.")

    script = adapt_script(blog_intro)

    async def _synth(text, voice, out_path):
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(out_path)

    with tempfile.TemporaryDirectory() as td:
        out_file = os.path.join(td, "voiceover.mp3")
        asyncio.run(_synth(script, config.TTS_VOICE, out_file))
        with open(out_file, "rb") as fh:
            data = fh.read()
    return data, script
