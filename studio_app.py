from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st

from studio.ai_providers import get_llm_provider
from studio.engine import (
    AVAILABLE_VOICES,
    audit_script_retention,
    compile_storyboard_to_broll_terms,
    create_social_package,
    delete_project_draft,
    fetch_research_pack,
    generate_hook_variations,
    generate_thumbnail_svg,
    list_saved_projects,
    load_project_draft,
    make_script,
    render_live_video_simulator,
    render_video_pipeline,
    replace_script_hook,
    run_council,
    save_project_draft,
    score_topics,
    segment_script_into_scenes,
)

st.set_page_config(
    page_title="Signal Studio · Embedded Video Engine",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

OUTPUTS_DIR = Path(__file__).parent / "studio_outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Manrope:wght@600;700;800;900&display=swap');

:root {
  --ink: #0d1411;
  --muted: #52605a;
  --paper: #f6f5ef;
  --card: #ffffff;
  --line: #dedbd2;
  --green: #14533d;
  --green-light: #e6f4ed;
  --lime: #d2f866;
  --amber: #d97706;
  --red: #dc2626;
}

.stApp { background: var(--paper); color: var(--ink); font-family: 'DM Sans', sans-serif; }
.block-container { max-width: 1440px; padding: 1rem 1.8rem 3rem; }
h1, h2, h3, h4, h5 { font-family: 'Manrope', sans-serif; letter-spacing: -0.03em; color: var(--ink); }

.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--line);
  padding: 0.2rem 0 0.8rem;
  margin-bottom: 1rem;
}

.brand-title {
  font: 900 1.25rem 'Manrope', sans-serif;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.brand-title b { color: var(--green); }

.badge-embedded {
  font-size: 0.72rem;
  font-weight: 800;
  padding: 0.3rem 0.75rem;
  border-radius: 99px;
  background: #dcfce7;
  color: #166534;
  border: 1px solid #86efac;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--card);
  border-color: var(--line) !important;
  border-radius: 14px !important;
  box-shadow: 0 2px 6px rgba(0,0,0,0.02);
}

.eyebrow {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--green);
  font-weight: 800;
  margin-bottom: 0.35rem;
}

.hook-chip {
  padding: 0.55rem 0.75rem;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #ffffff;
  margin-bottom: 0.45rem;
  font-size: 0.86rem;
  line-height: 1.35;
  transition: all 0.15s ease;
}

.hook-chip:hover { border-color: var(--green); background: #fafaf8; }

.stButton > button {
  border-radius: 8px;
  font-weight: 700;
  border: 1px solid var(--ink);
  min-height: 2.5rem;
}

.stButton > button[kind="primary"] {
  background: var(--green);
  border-color: var(--green);
  color: #ffffff;
}

.stButton > button[kind="primary"]:hover {
  background: #0f3d2d;
  border-color: #0f3d2d;
}
</style>""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar: Settings & Saved Drafts
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Engine Settings")
    llm_choice = st.selectbox("AI Engine", ["Demo (Zero Keys)", "Google Gemini", "OpenAI / Local Ollama"], index=0)
    gemini_key = st.text_input("Gemini API Key", value=os.getenv("GEMINI_API_KEY", ""), type="password") if llm_choice == "Google Gemini" else ""
    openai_key = st.text_input("OpenAI Key", value=os.getenv("OPENAI_API_KEY", ""), type="password") if llm_choice == "OpenAI / Local Ollama" else ""
    pexels_key = st.text_input("Pexels API Key (Optional)", value=os.getenv("PEXELS_API_KEY", ""), type="password", help="Leave blank to use curated offline stock media cache.")

    st.markdown("---")
    st.markdown("### 🗂️ Project Library")
    saved_projects = list_saved_projects(OUTPUTS_DIR)
    if saved_projects:
        proj_options = {p.get("project_id", ""): f"{p.get('topic', 'Untitled')[:24]} ({p.get('updated_at', '')[:10]})" for p in saved_projects}
        sel_p = st.selectbox("Drafts", list(proj_options.keys()), format_func=lambda k: proj_options.get(k, k))
        c1, c2 = st.columns(2)
        if c1.button("📂 Load", use_container_width=True):
            loaded = load_project_draft(sel_p, OUTPUTS_DIR)
            if loaded:
                for k, v in loaded.items():
                    if k in st.session_state: st.session_state[k] = v
                st.rerun()
        if c2.button("🗑️ Delete", use_container_width=True):
            delete_project_draft(sel_p, OUTPUTS_DIR)
            st.rerun()

current_llm = get_llm_provider(llm_choice, api_key=gemini_key or openai_key)

# ---------------------------------------------------------
# Session State Defaults
# ---------------------------------------------------------
defaults = {
    "niche": "AI productivity",
    "topic": "The 7-minute AI productivity workflow that gives creators their Fridays back",
    "tone_preset": "Balanced Editorial",
    "script": """Most people approach AI productivity by collecting more tools and adding friction to their day. I did too—and it only slowed down real progress.

So I tested a lean approach: one week, one repeatable workflow, and one rule: every automated step had to leave room for a human decision.

Step one: Start with the viewer's exact constraint, not a vague keyword.
Step two: Use AI to generate multiple competing angles, then filter aggressively for originality and practical proof.
Step three: Verify every claim and citation before any production button is pressed.

The surprising takeaway? The speed didn't come from removing human judgment—it came from having clear checkpoints where low-quality ideas get rejected immediately.

If you try this, start with a single video. Add something only you can contribute: an authentic test, a failure, or a measured comparison.

AI widens your options. Human judgment narrows them. That's the system that scales.""",
    "voice_model": "en-US-JennyNeural-Female",
    "aspect_ratio": "16:9",
    "hooks": [],
    "rendered_video_path": "",
    "render_message": "",
    "broll_tags": "creator desk, workflow diagram, editing timeline, screen capture",
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# ---------------------------------------------------------
# Top Navigation Bar
# ---------------------------------------------------------
st.markdown(
    '<div class="top-nav">'
    '<div class="brand-title"><b>🎬 SIGNAL STUDIO</b> <span>· Embedded MoneyPrinter Engine</span></div>'
    '<div class="badge-embedded">⚡ 100% IN-HOUSE MP4 RENDERER ACTIVE</div>'
    '</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Streamlined 2-Panel Workstation
# ---------------------------------------------------------
left_panel, right_panel = st.columns([1.1, 1.1], gap="large")

with left_panel:
    # 1. Brief & Topic
    with st.container(border=True):
        st.markdown('<div class="eyebrow">01 · Topic & Creative Brief</div>', unsafe_allow_html=True)
        col_a, col_b = st.columns([1, 1.5])
        st.session_state.niche = col_a.text_input("Niche", st.session_state.niche)
        st.session_state.topic = col_b.text_input("Video Topic", st.session_state.topic)

        gen_c1, gen_c2 = st.columns(2)
        if gen_c1.button("✨ Auto-Generate Storyboard", type="primary", use_container_width=True):
            with st.spinner("AI Council drafting angle & hooks..."):
                proposals, win_idx, _ = run_council(st.session_state.topic, st.session_state.niche, llm_provider=current_llm)
                selected = proposals[win_idx] if proposals else {}
                st.session_state.script = make_script(
                    topic=st.session_state.topic,
                    angle=selected.get("angle", ""),
                    thesis=selected.get("thesis", ""),
                    hook=selected.get("hook", ""),
                    niche=st.session_state.niche,
                    tone_preset=st.session_state.tone_preset,
                    llm_provider=current_llm,
                )
                st.session_state.hooks = generate_hook_variations(st.session_state.topic, st.session_state.niche, llm_provider=current_llm)
            st.rerun()

        if gen_c2.button("💾 Save Draft", use_container_width=True):
            save_project_draft({k: st.session_state[k] for k in defaults.keys()}, OUTPUTS_DIR)
            st.success("Draft saved!")

    # 2. Viral Hook Lab
    with st.container(border=True):
        st.markdown('<div class="eyebrow">02 · 3-Second Viral Hook Lab</div>', unsafe_allow_html=True)
        if not st.session_state.hooks:
            st.session_state.hooks = generate_hook_variations(st.session_state.topic, st.session_state.niche, llm_provider=current_llm)

        for h_i, h in enumerate(st.session_state.hooks[:3]):
            h_c1, h_c2 = st.columns([3.5, 1])
            h_c1.markdown(f'<div class="hook-chip"><b>{h["tag"]} ({h["hold_rate"]}% Hold):</b> "{h["hook"]}"</div>', unsafe_allow_html=True)
            if h_c2.button("Use Hook", key=f"btn_hook_{h_i}", use_container_width=True):
                st.session_state.script = replace_script_hook(st.session_state.script, h["hook"])
                st.success("Hook applied!")
                st.rerun()

    # 3. Narration Script & Tone
    with st.container(border=True):
        st.markdown('<div class="eyebrow">03 · Script Narration</div>', unsafe_allow_html=True)
        s_t1, s_t2 = st.columns([1.5, 1])
        tone_opts = ["Balanced Editorial", "Alex Hormozi Framework", "Veritasium Investigative Essay", "Viral Shorts / Reels"]
        st.session_state.tone_preset = s_t1.selectbox("Tone Preset", tone_opts, index=tone_opts.index(st.session_state.tone_preset) if st.session_state.tone_preset in tone_opts else 0)

        if s_t2.button("🔄 Rewrite Script", use_container_width=True):
            with st.spinner("Rewriting with selected tone..."):
                st.session_state.script = make_script(
                    topic=st.session_state.topic,
                    angle="Core Angle",
                    niche=st.session_state.niche,
                    tone_preset=st.session_state.tone_preset,
                    llm_provider=current_llm,
                )
            st.rerun()

        words = len(st.session_state.script.split())
        est_sec = round(words / 2.3)
        st.caption(f"📊 **{words} words** · ~**{est_sec}s** speaking duration")

        st.session_state.script = st.text_area("Narration Script", st.session_state.script, height=220, label_visibility="collapsed")

with right_panel:
    # 4. Interactive Live Simulator
    with st.container(border=True):
        st.markdown('<div class="eyebrow">04 · Live Interactive Video Simulator</div>', unsafe_allow_html=True)
        scenes = segment_script_into_scenes(st.session_state.script, target_clip_duration_sec=5)

        sim_html = render_live_video_simulator(
            scenes=scenes,
            title=st.session_state.topic,
            aspect_ratio=st.session_state.aspect_ratio,
        )
        st.components.v1.html(sim_html, height=400, scrolling=False)

    # 5. Direct In-App Video Rendering Engine
    with st.container(border=True):
        st.markdown('<div class="eyebrow">05 · In-House Video Render & Export Hub</div>', unsafe_allow_html=True)

        r1, r2 = st.columns(2)
        st.session_state.voice_model = r1.selectbox("Voice (Edge-TTS)", list(AVAILABLE_VOICES.keys()), index=0)
        st.session_state.aspect_ratio = r2.selectbox("Video Format", ["16:9", "9:16 (Shorts/Reels)"])

        render_progress = st.progress(0, text="Ready for instant rendering.")

        if st.button("🎬 RENDER FULL VIDEO (MP4)", type="primary", use_container_width=True):
            def on_progress(text: str, pct: float):
                render_progress.progress(int(pct * 100), text=text)

            with st.spinner("Executing in-house video rendering engine..."):
                settings = {
                    "voice_name": st.session_state.voice_model,
                    "voice_rate": 1.0,
                    "video_aspect": st.session_state.aspect_ratio.split()[0],
                    "video_clip_duration": 5,
                    "video_terms": compile_storyboard_to_broll_terms(scenes),
                }
                success, msg, out_path = render_video_pipeline(
                    topic=st.session_state.topic,
                    script=st.session_state.script,
                    settings=settings,
                    output_dir=OUTPUTS_DIR,
                    pexels_api_key=pexels_key,
                    progress_callback=on_progress,
                )
                st.session_state.render_message = msg
                if out_path and str(out_path).endswith(".mp4"):
                    st.session_state.rendered_video_path = str(out_path)

        if st.session_state.render_message:
            st.success(st.session_state.render_message)

        # In-App MP4 Player & Downloader
        if st.session_state.rendered_video_path and os.path.exists(st.session_state.rendered_video_path):
            st.markdown("##### 📺 Rendered Video Player")
            st.video(st.session_state.rendered_video_path)
            with open(st.session_state.rendered_video_path, "rb") as vf:
                st.download_button(
                    "⬇️ DOWNLOAD FINAL MP4 VIDEO",
                    data=vf.read(),
                    file_name=Path(st.session_state.rendered_video_path).name,
                    mime="video/mp4",
                    type="primary",
                    use_container_width=True,
                )

    # 6. Packaging & SEO Dropdown
    with st.expander("🎨 Thumbnail Mockup & Multi-Platform Social Packaging", expanded=False):
        svg_code = generate_thumbnail_svg(headline=st.session_state.topic, aspect_ratio=st.session_state.aspect_ratio.split()[0])
        st.markdown(svg_code, unsafe_allow_html=True)
        st.download_button("⬇️ Download SVG Thumbnail", data=svg_code, file_name="thumbnail.svg", mime="image/svg+xml")

        soc_pkg = create_social_package(
            topic=st.session_state.topic,
            script=st.session_state.script,
            niche=st.session_state.niche,
            research_claims=fetch_research_pack(st.session_state.topic),
            title=st.session_state.topic,
            tone_preset=st.session_state.tone_preset,
        )
        st.text_area("YouTube Description (with Chapters)", soc_pkg["youtube_description"], height=140)
        st.text_area("X / Twitter Thread", soc_pkg["x_post"], height=100)
