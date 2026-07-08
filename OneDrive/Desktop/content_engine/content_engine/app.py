"""
app.py
AI Content Engine - Streamlit shell.
Sidebar input form -> five-call base engine -> Pro extensions
(self-critique loop, voiceover, multi-channel adaptation).
"""

import streamlit as st

import config
import text_gen
import image_gen
import video_gen
import critic
import voiceover
import adapt

st.set_page_config(page_title="AI Content Engine", layout="wide")

# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------
for key in ["tagline", "blog", "social", "image_bytes", "image_prompt",
            "video_url", "motion_prompt", "verdict_log", "unresolved_flags",
            "voiceover_bytes", "voiceover_script", "adapted"]:
    if key not in st.session_state:
        st.session_state[key] = None

st.title("🚀 AI Content Engine")
st.caption("One brief in → a full campaign suite out — text, image, video, voiceover, and channel adaptation.")

missing_keys = config.check_keys()
if missing_keys:
    st.warning(
        f"Missing API keys: {', '.join(missing_keys)}. "
        f"Add them to your .env file before generating."
    )

# ---------------------------------------------------------------------------
# Sidebar form
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Campaign Brief")
    product = st.text_input("Product name", placeholder="e.g. EcoBrew Reusable Coffee Pods")
    audience = st.text_input("Target audience", placeholder="e.g. busy young professionals")
    tone = st.selectbox("Brand tone", config.TONE_OPTIONS)

    run_critique = st.checkbox("Run self-critique loop", value=True)
    make_voiceover = st.checkbox("Generate voiceover", value=False)

    generate_clicked = st.button("✨ Generate", type="primary", use_container_width=True)

    st.divider()
    st.subheader("Multi-Channel Adaptation")
    channel = st.selectbox("Adapt for channel", config.CHANNEL_OPTIONS)
    adapt_clicked = st.button("🔄 Adapt for this channel", use_container_width=True)

# ---------------------------------------------------------------------------
# Input validation (graceful handling of bad input)
# ---------------------------------------------------------------------------
def _inputs_valid(product, audience):
    if not product or not product.strip():
        st.error("Please enter a product name before generating.")
        return False
    if not audience or not audience.strip():
        st.error("Please enter a target audience before generating.")
        return False
    if len(product.strip()) < 2:
        st.error("Product name looks too short — please add more detail.")
        return False
    return True


# ---------------------------------------------------------------------------
# Main generation pipeline
# ---------------------------------------------------------------------------
if generate_clicked:
    if _inputs_valid(product, audience):
        try:
            with st.spinner("Generating tagline (few-shot)..."):
                tagline = text_gen.generate_tagline(product, audience, tone)

            with st.spinner("Writing blog intro (role-based)..."):
                blog = text_gen.generate_blog_intro(product, audience, tone, tagline)

            with st.spinner("Generating social posts (structured output)..."):
                social = text_gen.generate_social_post(product, audience, tone)

            verdict_log, unresolved_flags = None, []
            if run_critique:
                with st.spinner("Running self-critique loop..."):
                    tagline, blog, social, verdict_log, unresolved_flags = critic.run_critique_loop(
                        product, audience, tone, tagline, blog, social
                    )

            with st.spinner("Generating hero image..."):
                image_bytes, image_prompt = image_gen.generate_hero_image(product, tagline, tone)

            video_url, motion_prompt = None, None
            try:
                with st.spinner("Generating promo video (this can take a minute)..."):
                    video_url, motion_prompt = video_gen.generate_promo_video(image_bytes)
            except Exception as video_err:
                st.session_state["video_error"] = str(video_err)

            vo_bytes, vo_script = None, None
            if make_voiceover:
                try:
                    with st.spinner("Generating voiceover..."):
                        vo_bytes, vo_script = voiceover.generate_voiceover(blog)
                except Exception as vo_err:
                    st.session_state["voiceover_error"] = str(vo_err)

            # Persist everything to session state
            st.session_state.update({
                "tagline": tagline,
                "blog": blog,
                "social": social,
                "image_bytes": image_bytes,
                "image_prompt": image_prompt,
                "video_url": video_url,
                "motion_prompt": motion_prompt,
                "verdict_log": verdict_log,
                "unresolved_flags": unresolved_flags,
                "voiceover_bytes": vo_bytes,
                "voiceover_script": vo_script,
                "adapted": None,  # clear any stale adaptation
            })
            st.success("Campaign suite generated!")

        except Exception as e:
            st.error(f"Generation failed: {e}")

# ---------------------------------------------------------------------------
# Channel adaptation (Pro Addition 3)
# ---------------------------------------------------------------------------
if adapt_clicked:
    if not st.session_state["tagline"]:
        st.error("Generate a campaign suite first before adapting it for a channel.")
    else:
        try:
            with st.spinner(f"Adapting suite for {channel}..."):
                adapted = adapt.adapt_for_channel(
                    channel,
                    st.session_state["tagline"],
                    st.session_state["blog"],
                    st.session_state["social"],
                )
                st.session_state["adapted"] = adapted
                st.session_state["adapted_channel"] = channel
        except Exception as e:
            st.error(f"Channel adaptation failed: {e}")

# ---------------------------------------------------------------------------
# Display: two-column output layout
# ---------------------------------------------------------------------------
if st.session_state["tagline"]:
    col_text, col_visual = st.columns(2)

    with col_text:
        st.subheader("📝 Text Assets")

        flags = st.session_state["unresolved_flags"] or []

        st.markdown("**Tagline** _(few-shot prompting)_" + (" ⚠️" if "tagline" in flags else ""))
        st.info(st.session_state["tagline"])

        st.markdown("**Blog Intro** _(role-based prompting)_" + (" ⚠️" if "blog" in flags else ""))
        st.write(st.session_state["blog"])

        st.markdown("**Social Posts** _(structured output)_" + (" ⚠️" if "social" in flags else ""))
        social = st.session_state["social"]
        st.text_area("Twitter", social.get("twitter", ""), height=80)
        st.text_area("Instagram", social.get("instagram", ""), height=100)
        st.text_area("LinkedIn", social.get("linkedin", ""), height=100)

        if st.session_state["verdict_log"]:
            with st.expander("🔍 Self-critique verdicts"):
                for i, verdict in enumerate(st.session_state["verdict_log"]):
                    st.markdown(f"**Attempt {i + 1}**")
                    st.json(verdict)

        if st.session_state["adapted"]:
            with st.expander(f"🔄 Adapted for {st.session_state.get('adapted_channel', '')}"):
                adapted = st.session_state["adapted"]
                st.markdown("**Tagline**")
                st.info(adapted.get("tagline", ""))
                st.markdown("**Blog**")
                st.write(adapted.get("blog", ""))
                st.markdown("**Social**")
                st.json(adapted.get("social", {}))

    with col_visual:
        st.subheader("🎨 Visual & Audio Assets")

        st.markdown("**Hero Image** _(image prompt formula)_")
        st.image(st.session_state["image_bytes"], use_container_width=True)
        with st.expander("Image prompt used"):
            st.code(st.session_state["image_prompt"])

        st.markdown("**Promo Video** _(motion prompt → Runway)_")
        if st.session_state["video_url"]:
            st.video(st.session_state["video_url"])
            with st.expander("Motion prompt used"):
                st.code(st.session_state["motion_prompt"])
        elif st.session_state.get("video_error"):
            st.error(f"Video generation failed: {st.session_state['video_error']}")

        if make_voiceover or st.session_state["voiceover_bytes"]:
            st.markdown("**Voiceover** _(script adaptation → TTS)_")
            if st.session_state["voiceover_bytes"]:
                st.audio(st.session_state["voiceover_bytes"], format="audio/mp3")
                with st.expander("Voiceover script used"):
                    st.write(st.session_state["voiceover_script"])
                st.download_button(
                    "Download voiceover (.mp3)",
                    st.session_state["voiceover_bytes"],
                    file_name="voiceover.mp3",
                )
            elif st.session_state.get("voiceover_error"):
                st.error(f"Voiceover generation failed: {st.session_state['voiceover_error']}")
else:
    st.info("Fill in the brief on the left and click **Generate** to build your campaign suite.")
