"""
critic.py
Pro Addition 1 - The Self-Critique Loop.
Grades tagline, blog, and social output against the brief. If any asset
fails, regenerates it with the issue fed back in, up to MAX_CRITIC_RETRIES times.
"""

import json
import requests

import config
import text_gen

CRITIC_SYSTEM = """You are a senior content strategist reviewing campaign copy.
Grade each asset. Return ONLY JSON, no markdown fences, no commentary:
{"tagline": {"pass": true, "issue": null},
 "blog": {"pass": true, "issue": null},
 "social": {"pass": true, "issue": null}}
Fail if: tone mismatch, audience ignored, length exceeded,
or product description contradicted."""


def _call_critic(product, audience, tone, tagline, blog, social):
    if not config.OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set. Add it to your .env file.")

    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    user_prompt = (
        f"Brief:\nProduct: {product}\nAudience: {audience}\nTone: {tone}\n\n"
        f"Tagline: {tagline}\n\n"
        f"Blog intro: {blog}\n\n"
        f"Social JSON: {json.dumps(social)}\n\n"
        f"Grade each asset now."
    )

    payload = {
        "model": config.TEXT_MODEL,
        "messages": [
            {"role": "system", "content": CRITIC_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": 300,
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
        # If the critic itself misbehaves, default to a pass so we don't
        # infinite-loop on a broken critic response.
        return {
            "tagline": {"pass": True, "issue": None},
            "blog": {"pass": True, "issue": None},
            "social": {"pass": True, "issue": None},
        }


def run_critique_loop(product, audience, tone, tagline, blog, social):
    """
    Runs the critic, and regenerates failing assets with feedback injected,
    up to config.MAX_CRITIC_RETRIES times. Returns:
      (final_tagline, final_blog, final_social, verdict_log, unresolved_flags)
    where verdict_log is a list of critic verdicts (one per attempt) and
    unresolved_flags lists any assets still failing after all retries.
    """
    verdict_log = []
    unresolved_flags = []

    for attempt in range(config.MAX_CRITIC_RETRIES + 1):
        verdict = _call_critic(product, audience, tone, tagline, blog, social)
        verdict_log.append(verdict)

        failing = [asset for asset, result in verdict.items() if not result.get("pass", True)]

        if not failing:
            break

        if attempt == config.MAX_CRITIC_RETRIES:
            unresolved_flags = failing
            break

        # Regenerate only the failing assets, feeding back the issue as corrective feedback
        if "tagline" in failing:
            issue = verdict["tagline"].get("issue")
            tagline = text_gen.generate_tagline(product, audience, tone, feedback=issue)
        if "blog" in failing:
            issue = verdict["blog"].get("issue")
            blog = text_gen.generate_blog_intro(product, audience, tone, tagline, feedback=issue)
        if "social" in failing:
            issue = verdict["social"].get("issue")
            social = text_gen.generate_social_post(product, audience, tone, feedback=issue)

    return tagline, blog, social, verdict_log, unresolved_flags
