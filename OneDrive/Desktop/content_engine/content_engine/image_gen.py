"""
image_gen.py
Builds the hero image prompt using the subject + style + composition + constraints
formula, then calls the GPT Image API to generate the image.
"""

import base64
import requests

import config


def build_image_prompt(product, tagline, tone):
    """Programmatic image prompt: subject + style (from tone) + composition + constraints."""
    style = config.STYLE_MAP.get(tone, config.DEFAULT_STYLE)
    return (
        f"A {style} of {product}. "
        f"Centred, shallow depth of field, 16:9 composition. "
        f"No text, no logos, no watermarks."
    )


def generate_hero_image(product, tagline, tone):
    """
    Calls the GPT Image API and returns raw image bytes (PNG).
    Requires GPT_IMAGE_API_KEY (defaults to OPENROUTER_API_KEY if unset in .env,
    but note: image generation typically needs a direct OpenAI-compatible key).
    """
    if not config.GPT_IMAGE_BASE_URL:
        raise RuntimeError("GPT_IMAGE_BASE_URL is not set. Add it to your .env file.")

    prompt = build_image_prompt(product, tagline, tone)

    # If GPT_IMAGE_BASE_URL points to a Hugging Face model inference endpoint,
    # the API returns raw image bytes for many models. Use the HF token in header if provided.
    headers = {}
    if config.GPT_IMAGE_API_KEY:
        headers["Authorization"] = f"Bearer {config.GPT_IMAGE_API_KEY}"

    # HF inference: POST the prompt as JSON or text depending on the model. We'll try JSON.
    hf_payload = {"inputs": prompt}

    resp = requests.post(
        config.GPT_IMAGE_BASE_URL,
        headers=headers,
        json=hf_payload,
        timeout=120,
    )

    # If Hugging Face returns binary image bytes, resp.content is the image.
    content_type = resp.headers.get("Content-Type", "")
    if resp.status_code == 200 and content_type.startswith("image"):
        return resp.content, prompt

    # Otherwise try to parse JSON response — some HF models return base64 in JSON
    resp.raise_for_status()
    data = resp.json()

    # Common HF format: {'generated_image': <base64 string>} or list of dicts
    # Try a few possibilities defensively.
    b64_data = None
    if isinstance(data, dict):
        for key in ("generated_image", "image", "data"):
            if key in data and isinstance(data[key], str):
                b64_data = data[key]
                break
        # Sometimes HF returns {'data': [{'b64_json': '...'}]}
        if not b64_data and "data" in data and isinstance(data["data"], list):
            first = data["data"][0]
            if isinstance(first, dict) and "b64_json" in first:
                b64_data = first["b64_json"]
    elif isinstance(data, list) and data and isinstance(data[0], dict):
        first = data[0]
        if "b64_json" in first:
            b64_data = first["b64_json"]

    if b64_data:
        return base64.b64decode(b64_data), prompt

    # As a last resort, raise with the raw JSON for debugging
    raise RuntimeError(f"Unexpected image generation response: {data}")
