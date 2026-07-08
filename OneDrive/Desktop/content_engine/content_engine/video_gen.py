"""
video_gen.py
Feeds the hero image into Runway with a gentle motion prompt to produce
a short (5-8 second) promotional video clip.
"""

import base64
import time
import requests

import config

MOTION_PROMPT = (
    "Slow cinematic push-in. "
    "Soft light shifts gently. "
    "Background mostly still. 5 seconds."
)


def _image_bytes_to_data_uri(image_bytes, mime_type="image/png"):
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{b64}"


def generate_promo_video(image_bytes, poll_interval=5, max_wait=300):
    """
    Submits an image-to-video job to Runway, polls until complete,
    and returns the resulting video URL.
    """
    if not config.RUNWAY_API_KEY:
        raise RuntimeError("REPLICATE_API_TOKEN (RUNWAY_API_KEY) is not set. Add it to your .env file.")

    # Replicate-style prediction: create a prediction, poll until succeeded, then return output
    headers = {
        "Authorization": f"Token {config.RUNWAY_API_KEY}",
        "Content-Type": "application/json",
    }

    # Upload the image to a short-lived endpoint if necessary; many Replicate models accept base64 or urls.
    payload = {
        "version": config.RUNWAY_MODEL,
        "input": {
            "image": _image_bytes_to_data_uri(image_bytes),
            "prompt": MOTION_PROMPT,
            "duration": 5,
            "ratio": "1280:720",
        },
    }

    submit = requests.post(
        f"{config.RUNWAY_BASE_URL}/predictions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    submit.raise_for_status()
    pred = submit.json()
    pred_id = pred.get("id") or pred.get("prediction", {}).get("id")

    if not pred_id:
        # Some responses embed the status under 'prediction'
        pred_id = pred.get("id")

    elapsed = 0
    while elapsed < max_wait:
        status_resp = requests.get(
            f"{config.RUNWAY_BASE_URL}/predictions/{pred_id}",
            headers=headers,
            timeout=30,
        )
        status_resp.raise_for_status()
        status_data = status_resp.json()
        status = status_data.get("status") or status_data.get("prediction", {}).get("status")

        if status in ("succeeded", "SUCCEEDED"):
            # Replicate returns output as a list of urls or data under 'output'
            output = status_data.get("output") or status_data.get("prediction", {}).get("output")
            # Return first output item if it's a URL
            if isinstance(output, list):
                return output[0], MOTION_PROMPT
            return output, MOTION_PROMPT
        if status in ("failed", "FAILED", "canceled"):
            raise RuntimeError(f"Video generation failed: {status_data}")

        time.sleep(poll_interval)
        elapsed += poll_interval

    raise TimeoutError("Video generation timed out.")
