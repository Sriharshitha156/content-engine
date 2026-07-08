"""
text_gen.py
The three text-generation calls: tagline (few-shot), blog intro (role-based),
social post (structured JSON output). All three route through OpenRouter.
"""

import json
import requests

import config

# ---------------------------------------------------------------------------
# Few-shot examples per tone, used to calibrate the tagline call.
# ---------------------------------------------------------------------------
TAGLINE_FEW_SHOTS = {
    "playful": [
        ("Colourful reusable water bottles", "Sip happy. Live loud."),
        ("A kids' building-blocks app", "Build worlds. Break boredom."),
    ],
    "premium": [
        ("Handmade Italian leather bags", "Crafted for a lifetime, not a season."),
        ("A private wealth management app", "Wealth, quietly mastered."),
    ],
    "eco": [
        ("Compostable packaging line", "Nothing wasted. Everything returned."),
        ("Solar-powered home chargers", "Power that gives back."),
    ],
    "clean modern": [
        ("A minimalist productivity app", "Less noise. More done."),
        ("A modern furniture brand", "Design that gets out of the way."),
    ],
}

TAGLINE_SYSTEM = """You are a creative director. Generate ONE campaign tagline.
Match the brand tone exactly. Max 10 words. No hashtags. No quotation marks.
Return only the tagline text, nothing else."""

BLOG_SYSTEM = """You are a content strategist writing for {audience}.
Write a 200-word blog intro for {product}.
Weave in the campaign tagline: "{tagline}".
Tone: {tone}.
Return only the blog intro text, nothing else."""

SOCIAL_SYSTEM = """Generate social posts for {product}. Return ONLY JSON, no markdown fences, no commentary:
{{"twitter": "string, max 280 chars", "instagram": "string, max 2200 chars", "linkedin": "string, max 700 chars"}}
Tone: {tone}. Audience: {audience}."""


def _call_openrouter(system_prompt, user_prompt, max_tokens=600):
    """Shared helper for chat completions via OpenRouter."""
    if not config.OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set. Add it to your .env file.")
    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.TEXT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
    }

    # DeepSeek follows a similar OpenAI-style chat completions endpoint.
    resp = requests.post(
        f"{config.OPENROUTER_BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def generate_tagline(product, audience, tone, feedback=None):
    """Few-shot prompted tagline generation."""
    examples = TAGLINE_FEW_SHOTS.get(tone, TAGLINE_FEW_SHOTS["clean modern"])
    example_block = "\n".join(
        f'Product: {ex_product}\nTagline: {ex_tagline}' for ex_product, ex_tagline in examples
    )

    user_prompt = (
        f"Here are examples of taglines in a {tone} tone:\n\n{example_block}\n\n"
        f"Now write a tagline for:\nProduct: {product}\nAudience: {audience}\nTone: {tone}"
    )
    if feedback:
        user_prompt += f"\n\nA previous attempt failed review for this reason: {feedback}\nFix this in your new tagline."

    return _call_openrouter(TAGLINE_SYSTEM, user_prompt, max_tokens=60)


def generate_blog_intro(product, audience, tone, tagline, feedback=None):
    """Role-based blog intro generation, 200 words, weaves in the tagline."""
    system_prompt = BLOG_SYSTEM.format(audience=audience, product=product, tagline=tagline, tone=tone)
    user_prompt = f"Write the 200-word blog intro now."
    if feedback:
        user_prompt += f"\n\nA previous attempt failed review for this reason: {feedback}\nFix this in your new version."

    return _call_openrouter(system_prompt, user_prompt, max_tokens=400)


def generate_social_post(product, audience, tone, feedback=None):
    """Structured JSON output: twitter / instagram / linkedin variants."""
    system_prompt = SOCIAL_SYSTEM.format(product=product, tone=tone, audience=audience)
    user_prompt = "Generate the JSON now."
    if feedback:
        user_prompt += f"\n\nA previous attempt failed review for this reason: {feedback}\nFix this in your new version."

    raw = _call_openrouter(system_prompt, user_prompt, max_tokens=500)

    # Defensive cleanup in case the model wraps the JSON in markdown fences anyway
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fall back to a safe structure so the UI doesn't crash
        return {
            "twitter": cleaned[:280],
            "instagram": cleaned[:2200],
            "linkedin": cleaned[:700],
        }
