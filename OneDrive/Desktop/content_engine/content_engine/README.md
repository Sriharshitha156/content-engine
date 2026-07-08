
# AI Content Engine (Lab + Pro Extensions)

One product brief in → a complete campaign suite out: tagline, blog intro,
social posts, hero image, promo video, voiceover, and channel adaptation.

## What's inside

| File | Purpose |
|---|---|
| `app.py` | Streamlit shell — sidebar form, two-column layout, orchestration |
| `text_gen.py` | Tagline (few-shot), blog intro (role-based), social post (structured JSON) |
| `image_gen.py` | Hero image prompt formula + GPT Image API call |
| `video_gen.py` | Motion prompt + Runway image-to-video call |
| `critic.py` | **Pro Addition 1** — self-critique loop with auto-regeneration |
| `voiceover.py` | **Pro Addition 2** — script adaptation + TTS voiceover |
| `adapt.py` | **Pro Addition 3** — multi-channel text adaptation |
| `config.py` | API keys + model settings, loaded from `.env` |

## Setup (Windows / PowerShell)

```powershell
# 1. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up your .env file
Copy-Item .env.example .env
notepad .env   # fill in your real API keys and save

# 4. Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## API keys you need

- **OPENROUTER_API_KEY** — powers tagline, blog, social, critic, script adapter, and channel adaptation calls
- **GPT_IMAGE_API_KEY** — powers the hero image call (OpenAI-compatible `/images/generations` endpoint)
- **RUNWAY_API_KEY** — powers the image-to-video call
- **TTS_API_KEY** — powers the voiceover call (OpenAI-compatible `/audio/speech` endpoint)

If a key is missing, the app shows a warning banner and the relevant card shows
an inline error instead of crashing the rest of the run.

## How the chain works

1. **Tagline** (few-shot) →
2. **Blog intro** (role-based, weaves in the tagline) →
3. **Social post** (structured JSON, platform-specific limits)
4. *(optional)* **Self-critique loop** grades all three, regenerates failures with feedback, max 2 retries
5. **Hero image** (built from product + tagline + tone) →
6. **Promo video** (hero image + motion prompt via Runway)
7. *(optional)* **Voiceover** (blog intro → TTS-ready script → audio)
8. *(optional)* **Channel adaptation** (rewrites tagline/blog/social for a chosen channel; image + video stay unchanged)

## Notes on Windows / CRLF

If you run a linter or formatter (e.g. Prettier, Black) across this project,
scope it to changed files only rather than the whole repo — Windows-created
files often carry CRLF line endings that will otherwise surface as noisy,
unrelated diffs.

## Reflection: hardest addition & what RAG/agents would improve

The self-critique loop was the trickiest addition — the critic itself is just
another LLM call, so it can misjudge or return malformed JSON. The current
implementation defaults to "pass" if the critic's own output fails to parse,
which avoids infinite loops but means a broken critic silently stops
catching real issues.

- **Retrieval (RAG)** would help by grounding the critic and generation
  prompts in actual brand guidelines, past approved campaigns, or a style
  guide, rather than relying purely on the tone label to infer what "on brand"
  means.
- **Agentic patterns** would help by letting the critic call tools (e.g. a
  word-counter, a brand-lexicon checker) for objective checks like length and
  banned-word violations, reserving the LLM judgment for subjective quality
  (voice, persuasiveness), rather than asking one model call to do both.

## Stretch ideas not yet implemented

- A/B tagline testing with LLM-as-judge
- Exportable campaign brief PDF
- Token/cost tracker per call
- Multilingual regeneration
