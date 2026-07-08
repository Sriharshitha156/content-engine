"""
adapt.py
Pro Addition 3 - Multi-Channel Adaptation.
Rewrites tagline, blog, and social assets for a chosen channel
(B2B LinkedIn / Gen-Z TikTok / Parents Facebook). Image and video
are left untouched - this is a text-only transformation.
"""

import json
import requests

import config

ADAPT_SYSTEM = """Rewrite these three assets for {channel}:
1. Tagline: {tagline}
2. Blog: {blog}
3. Social: {social_json}
Adapt tone, vocabulary, and emoji usage for the target channel.
Return ONLY JSON, no markdown fences, no commentary:
{{"tagline": "string", "blog": "string", "social": {{"twitter": "string", "instagram": "string", "linkedin": "string"}}}}"""


def adapt_for_channel(channel, tagline, blog, social):
    """Returns a dict: {"tagline": ..., "blog": ..., "social": {...}}"""
    if not config.OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set. Add it to your .env file.")

    system_prompt = ADAPT_SYSTEM.format(
        channel=channel,
        tagline=tagline,
        blog=blog,
        social_json=json.dumps(social),
    )

    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.TEXT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Adapt the assets now."},
        ],
        "max_tokens": 700,
    }

    resp = requests.post(
        f"{config.OPENROUTER_BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    raw = resp.json()["choices"][0]["message"]["content"].strip()

    cleaned = raw.strip("`")
    if cleaned.lower().startswith("json"):
        cleaned = cleaned[4:].strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: return originals unchanged rather than crashing the UI
        return {"tagline": tagline, "blog": blog, "social": social}
