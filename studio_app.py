from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

import streamlit as st

from studio.ai_providers import get_llm_provider
from studio.engine import (
    AVAILABLE_VOICES,
    audit_script_retention,
    compile_storyboard_to_broll_terms,
    create_social_package,
    delete_project_draft,
    fetch_live_youtube_competitors,
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
    page_title="SIGNAL STUDIO · Autonomous AI Video Suite",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

OUTPUTS_DIR = Path(__file__).parent / "studio_outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------
# Secure Key Resolver
# ---------------------------------------------------------
def get_secure_key(name: str) -> str:
    """Retrieve sensitive API credentials safely from Streamlit secrets or OS environment."""
    if hasattr(st, "secrets") and name in st.secrets:
        return str(st.secrets[name]).strip()
    return os.getenv(name, "").strip()

AUTO_GEMINI_KEY = get_secure_key("GEMINI_API_KEY") or get_secure_key("GOOGLE_API_KEY")
AUTO_YT_KEY = get_secure_key("YOUTUBE_API_KEY") or AUTO_GEMINI_KEY

# ---------------------------------------------------------
# High-Contrast Obsidian Studio Design System
# ---------------------------------------------------------
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Outfit:wght@600;700;800;900&family=Space+Grotesk:wght@600;700&display=swap');

:root {
  --bg-deep: #080d1a;
  --bg-card: #0f172a;
  --bg-card-subtle: #1e293b;
  --border-card: #334155;
  --text-primary: #ffffff;
  --text-secondary: #cbd5e1;
  --text-muted: #94a3b8;
  --emerald-main: #10b981;
  --emerald-glow: rgba(16, 185, 129, 0.3);
  --cyan-main: #06b6d4;
  --amber-main: #f59e0b;
}

/* Base Body Contrast */
.stApp {
  background-color: var(--bg-deep);
  color: var(--text-primary);
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.block-container {
  max-width: 1520px;
  padding: 1rem 2rem 4rem;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
  font-family: 'Outfit', sans-serif;
  letter-spacing: -0.025em;
  color: #ffffff !important;
  font-weight: 800;
}

/* Card Wrappers */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--bg-card);
  border: 1px solid var(--border-card) !important;
  border-radius: 16px !important;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
  padding: 1.1rem 1.35rem;
  margin-bottom: 0.5rem;
}

/* Top Navigation Bar */
.pro-navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-card);
  padding: 0.5rem 0 1.2rem;
  margin-bottom: 1.2rem;
}

.brand-badge {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-family: 'Outfit', sans-serif;
  font-size: 1.4rem;
  font-weight: 900;
  color: #ffffff;
}

.brand-badge span {
  color: var(--emerald-main);
  text-shadow: 0 0 14px var(--emerald-glow);
}

.engine-status-pill {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.78rem;
  font-weight: 800;
  padding: 0.4rem 0.95rem;
  border-radius: 99px;
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.4);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.engine-status-pill::before {
  content: "";
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 10px #10b981;
}

/* Eyebrow Label */
.eyebrow {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.74rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--emerald-main);
  font-weight: 800;
  margin-bottom: 0.6rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

/* Hook Card */
.hook-card {
  padding: 0.75rem 1rem;
  border: 1px solid var(--border-card);
  border-radius: 12px;
  background: rgba(30, 41, 59, 0.7);
  margin-bottom: 0.6rem;
  color: #ffffff;
  font-size: 0.9rem;
  line-height: 1.45;
  transition: all 0.2s ease;
}

.hook-card:hover {
  border-color: var(--emerald-main);
  background: rgba(16, 185, 129, 0.08);
}

.hook-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.35rem;
}

.hook-tag {
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--cyan-main);
}

.hold-rate-badge {
  font-size: 0.75rem;
  font-weight: 800;
  padding: 0.2rem 0.55rem;
  border-radius: 6px;
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.4);
}

/* Competitor Radar Row */
.competitor-row {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  padding: 0.7rem 0.9rem;
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid var(--border-card);
  border-radius: 12px;
  margin-bottom: 0.6rem;
}

.comp-img {
  width: 96px;
  height: 56px;
  border-radius: 8px;
  object-fit: cover;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.comp-content {
  flex: 1;
  min-width: 0;
}

.comp-title {
  font-size: 0.88rem;
  font-weight: 700;
  color: #ffffff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.comp-meta {
  font-size: 0.78rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

/* Storyboard Scene Card */
.scene-grid-card {
  background: rgba(30, 41, 59, 0.85);
  border: 1px solid var(--border-card);
  border-radius: 10px;
  padding: 0.65rem 0.85rem;
  margin-bottom: 0.5rem;
}

.scene-grid-header {
  display: flex;
  justify-content: space-between;
  font-size: 0.76rem;
  font-weight: 800;
  color: var(--emerald-main);
  margin-bottom: 0.25rem;
}

.scene-grid-body {
  font-size: 0.82rem;
  color: #f1f5f9;
  line-height: 1.35;
}

/* Retention Gauge Meter */
.retention-bar-wrapper {
  background: rgba(30, 41, 59, 0.85);
  border: 1px solid var(--border-card);
  border-radius: 12px;
  padding: 0.85rem 1.1rem;
  margin-bottom: 0.85rem;
}

.retention-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.86rem;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 0.45rem;
}

.retention-fill-track {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 99px;
  overflow: hidden;
}

.retention-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #06b6d4);
  border-radius: 99px;
}

/* Buttons */
.stButton > button {
  border-radius: 10px;
  font-weight: 700;
  font-size: 0.92rem;
  min-height: 2.75rem;
  border: 1px solid var(--border-card);
  background: #1e293b;
  color: #ffffff;
}

.stButton > button:hover {
  background: #334155;
  border-color: rgba(255, 255, 255, 0.3);
}

.stButton > button[kind="primary"] {
  background: var(--emerald-main);
  border-color: var(--emerald-main);
  color: #04100c !important;
  font-weight: 800;
  box-shadow: 0 4px 18px rgba(16, 185, 129, 0.35);
}

.stButton > button[kind="primary"]:hover {
  background: #34d399;
  border-color: #34d399;
  box-shadow: 0 6px 24px rgba(16, 185, 129, 0.5);
}
</style>""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar: Settings & Live Credentials
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ Studio Control Engine")

    llm_choice = st.selectbox("AI Intelligence Tier", ["Google Gemini 2.5 (Active)", "OpenAI / Local Ollama", "Demo Sandbox"], index=0)

    gemini_key = AUTO_GEMINI_KEY
    if not gemini_key and "Gemini" in llm_choice:
        gemini_key = st.text_input("Gemini API Key", type="password", help="Enter your Google Gemini API key.")
    elif gemini_key and "Gemini" in llm_choice:
        st.caption(f"🔒 **Gemini Key Active:** `••••••••{gemini_key[-5:]}`")

    openai_key = get_secure_key("OPENAI_API_KEY")
    if "OpenAI" in llm_choice:
        openai_key = st.text_input("OpenAI Key", value=openai_key, type="password")

    st.markdown("---")
    st.markdown("#### 📡 Market Intelligence APIs")
    yt_key = AUTO_YT_KEY
    if yt_key:
        st.caption(f"🟢 **YouTube Data API Connected:** `••••••••{yt_key[-5:]}`")
    else:
        yt_key = st.text_input("YouTube Data API Key", type="password", help="Fetches live competitor view counts & rankings.")

    pexels_key = get_secure_key("PEXELS_API_KEY")
    if not pexels_key:
        pexels_key = st.text_input("Pexels Key (Optional)", type="password", help="Leave blank for built-in curated HD stock engine.")

    st.markdown("---")
    st.markdown("#### 🗂️ Project Library")
    saved_projects = list_saved_projects(OUTPUTS_DIR)
    if saved_projects:
        proj_options = {p.get("project_id", ""): f"{p.get('topic', 'Untitled')[:22]} ({p.get('updated_at', '')[:10]})" for p in saved_projects}
        sel_p = st.selectbox("Saved Drafts", list(proj_options.keys()), format_func=lambda k: proj_options.get(k, k))
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

current_llm = get_llm_provider("gemini" if "Gemini" in llm_choice else llm_choice, api_key=gemini_key or openai_key)

# ---------------------------------------------------------
# State Defaults
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
    "aspect_ratio": "9:16 (Shorts/TikTok/Reels)",
    "video_pacing": "🎬 Standard (5s Cuts)",
    "subtitle_style": "🟡 Hormozi Pop (Gold/Emerald)",
    "hooks": [],
    "competitors": [],
    "rendered_video_path": "",
    "rendered_audio_path": "",
    "rendered_srt_path": "",
    "render_message": "",
    "broll_tags": "creator desk, workflow diagram, editing timeline, screen capture",
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# ---------------------------------------------------------
# Top Studio Header
# ---------------------------------------------------------
st.markdown(
    '<div class="pro-navbar">'
    '<div class="brand-badge">🎬 SIGNAL STUDIO <span>· PRO</span></div>'
    '<div class="engine-status-pill">● PRODUCTION VIDEO ENGINE ONLINE</div>'
    '</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 2-Panel Production Creator Workstation
# ---------------------------------------------------------
left_panel, right_panel = st.columns([1.15, 1.1], gap="large")

with left_panel:
    # 1. Brief & Topic
    with st.container(border=True):
        st.markdown('<div class="eyebrow">01 · Topic Brief & Live Market Radar</div>', unsafe_allow_html=True)
        col_a, col_b = st.columns([1, 1.6])
        st.session_state.niche = col_a.text_input("Creator Niche", st.session_state.niche)
        st.session_state.topic = col_b.text_input("Core Video Topic", st.session_state.topic)

        gen_c1, gen_c2 = st.columns(2)
        if gen_c1.button("✨ Auto-Generate Storyboard", type="primary", use_container_width=True):
            with st.spinner("Analyzing live YouTube competitor radar & executing AI Council..."):
                st.session_state.competitors = fetch_live_youtube_competitors(
                    query=st.session_state.topic,
                    api_key=yt_key,
                    limit=3,
                )
                citations = fetch_research_pack(topic=st.session_state.topic)

                proposals, win_idx, _ = run_council(
                    st.session_state.topic,
                    st.session_state.niche,
                    llm_provider=current_llm,
                    competitors=st.session_state.competitors,
                    citations=citations,
                )
                selected = proposals[win_idx] if proposals else {}
                st.session_state.script = make_script(
                    topic=st.session_state.topic,
                    angle=selected.get("angle", ""),
                    thesis=selected.get("thesis", ""),
                    hook=selected.get("hook", ""),
                    niche=st.session_state.niche,
                    tone_preset=st.session_state.tone_preset,
                    llm_provider=current_llm,
                    competitors=st.session_state.competitors,
                    citations=citations,
                )
                st.session_state.hooks = generate_hook_variations(st.session_state.topic, st.session_state.niche, llm_provider=current_llm)
            st.rerun()

        if gen_c2.button("💾 Save Project Draft", use_container_width=True):
            save_project_draft({k: st.session_state[k] for k in defaults.keys()}, OUTPUTS_DIR)
            st.success("Project draft saved to local library!")

    # 1.5 Live Competitor Radar
    if not st.session_state.competitors:
        st.session_state.competitors = fetch_live_youtube_competitors(st.session_state.topic, api_key=yt_key, limit=3)

    if st.session_state.competitors:
        with st.container(border=True):
            st.markdown('<div class="eyebrow">📡 Live YouTube Competitor Radar</div>', unsafe_allow_html=True)
            for comp in st.session_state.competitors[:3]:
                st.markdown(
                    f"""<div class="competitor-row">
                      <img src="{comp.get('thumbnail')}" class="comp-img" />
                      <div class="comp-content">
                        <div class="comp-title">{comp.get('title')}</div>
                        <div class="comp-meta">📺 {comp.get('channel')} · 🔥 {comp.get('views')} · <a href="{comp.get('url')}" target="_blank" style="color:#06b6d4; font-weight:700;">Watch on YouTube ↗</a></div>
                      </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

    # 2. Viral Hook A/B Lab
    with st.container(border=True):
        st.markdown('<div class="eyebrow">02 · 3-Second Viral Hook A/B Lab</div>', unsafe_allow_html=True)
        if not st.session_state.hooks:
            st.session_state.hooks = generate_hook_variations(st.session_state.topic, st.session_state.niche, llm_provider=current_llm)

        for h_i, h in enumerate(st.session_state.hooks[:3]):
            h_c1, h_c2 = st.columns([3.6, 1])
            with h_c1:
                st.markdown(
                    f"""<div class="hook-card">
                      <div class="hook-meta">
                        <span class="hook-tag">[{h['archetype']}] {h['tag']}</span>
                        <span class="hold-rate-badge">🔥 {h['hold_rate']}% Hold Rate</span>
                      </div>
                      <div>"{h['hook']}"</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with h_c2:
                if st.button("Apply Hook", key=f"btn_hook_{h_i}", use_container_width=True):
                    st.session_state.script = replace_script_hook(st.session_state.script, h["hook"])
                    st.success("Hook applied!")
                    st.rerun()

    # 3. Narration Script & Tone
    with st.container(border=True):
        st.markdown('<div class="eyebrow">03 · Script Narration & Tone Presets</div>', unsafe_allow_html=True)

        s_t1, s_t2 = st.columns([1.5, 1])
        tone_opts = ["Balanced Editorial", "Alex Hormozi Framework", "Veritasium Investigative Essay", "Viral Shorts / Reels"]
        st.session_state.tone_preset = s_t1.selectbox("Creator Tone Style", tone_opts, index=tone_opts.index(st.session_state.tone_preset) if st.session_state.tone_preset in tone_opts else 0)

        if s_t2.button("🔄 Rewrite with Tone", use_container_width=True):
            with st.spinner("Rewriting script with selected creator framework..."):
                citations = fetch_research_pack(st.session_state.topic)
                st.session_state.script = make_script(
                    topic=st.session_state.topic,
                    angle="Core Differentiated Angle",
                    niche=st.session_state.niche,
                    tone_preset=st.session_state.tone_preset,
                    llm_provider=current_llm,
                    competitors=st.session_state.competitors,
                    citations=citations,
                )
            st.rerun()

        ret_audit = audit_script_retention(st.session_state.script)
        words = len(st.session_state.script.split())
        est_sec = round(words / 2.3)
        ret_score = ret_audit.get("score", 85)

        st.markdown(
            f"""<div class="retention-bar-wrapper">
              <div class="retention-stats">
                <span>🎯 Retention Score: {ret_score}/100</span>
                <span>⏱️ ~{est_sec}s spoken ({words} words)</span>
              </div>
              <div class="retention-fill-track">
                <div class="retention-fill" style="width: {ret_score}%;"></div>
              </div>
            </div>""",
            unsafe_allow_html=True,
        )

        st.session_state.script = st.text_area("Narration Script", st.session_state.script, height=210, label_visibility="collapsed")

    # 3.5 Multi-Scene Storyboard Breakdown
    target_clip_sec = 3 if "3s" in st.session_state.video_pacing else 8 if "8s" in st.session_state.video_pacing else 5
    scenes = segment_script_into_scenes(st.session_state.script, target_clip_duration_sec=target_clip_sec)

    with st.expander(f"🎬 Scene-by-Scene Multi-Clip Timeline ({len(scenes)} Scenes)", expanded=False):
        for sc in scenes:
            st.markdown(
                f"""<div class="scene-grid-card">
                  <div class="scene-grid-header">
                    <span>SCENE {sc['scene_idx']:02d} [{sc['time_label']}]</span>
                    <span>TAGS: {sc['broll_query']}</span>
                  </div>
                  <div class="scene-grid-body"><b>Visual:</b> {sc['visual_concept']}</div>
                </div>""",
                unsafe_allow_html=True,
            )

with right_panel:
    # 4. Multi-Format Video Customization Matrix
    with st.container(border=True):
        st.markdown('<div class="eyebrow">04 · Video Format & Style Customizer</div>', unsafe_allow_html=True)
        vf_1, vf_2, vf_3 = st.columns(3)

        aspect_opts = ["9:16 (Shorts/TikTok/Reels)", "16:9 (YouTube Widescreen)", "1:1 (Square Feed)"]
        st.session_state.aspect_ratio = vf_1.selectbox("Format / Aspect", aspect_opts, index=aspect_opts.index(st.session_state.aspect_ratio) if st.session_state.aspect_ratio in aspect_opts else 0)

        pacing_opts = ["⚡ Fast (3s Viral Cuts)", "🎬 Standard (5s Flow)", "📽️ Cinematic (8s Deep Dive)"]
        st.session_state.video_pacing = vf_2.selectbox("Scene Cut Pacing", pacing_opts, index=pacing_opts.index(st.session_state.video_pacing) if st.session_state.video_pacing in pacing_opts else 1)

        sub_opts = ["🟡 Hormozi Pop (Gold/Emerald)", "🔴 MrBeast Impact (Bold Red)", "🔵 Cyber Cyan", "⚪ Clean Minimalist"]
        st.session_state.subtitle_style = vf_3.selectbox("Subtitle Styling", sub_opts, index=sub_opts.index(st.session_state.subtitle_style) if st.session_state.subtitle_style in sub_opts else 0)

    # 4.5 Interactive Live Simulator
    with st.container(border=True):
        st.markdown('<div class="eyebrow">04.5 · Live Interactive Video Simulator</div>', unsafe_allow_html=True)

        sim_html = render_live_video_simulator(
            scenes=scenes,
            title=st.session_state.topic,
            aspect_ratio=st.session_state.aspect_ratio.split()[0],
            subtitle_style=st.session_state.subtitle_style.split()[1].lower(),
        )
        sim_height = 580 if "9:16" in st.session_state.aspect_ratio else 450
        st.components.v1.html(sim_html, height=sim_height, scrolling=False)

    # 5. Native In-House MP4 Video Rendering Engine
    with st.container(border=True):
        st.markdown('<div class="eyebrow">05 · In-House Video Render & Export Hub</div>', unsafe_allow_html=True)

        st.session_state.voice_model = st.selectbox("Neural Voiceover (Edge-TTS)", list(AVAILABLE_VOICES.keys()), index=0)

        render_progress = st.progress(0, text="Ready for instant rendering.")

        if st.button("🎬 RENDER PRODUCTION MP4 VIDEO", type="primary", use_container_width=True):
            def on_progress(text: str, pct: float):
                render_progress.progress(int(pct * 100), text=text)

            with st.spinner("Executing in-house video rendering engine..."):
                settings = {
                    "voice_name": st.session_state.voice_model,
                    "voice_rate": 1.0,
                    "video_aspect": st.session_state.aspect_ratio.split()[0],
                    "video_clip_duration": target_clip_sec,
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
                if out_path:
                    p_str = str(out_path)
                    if p_str.endswith(".mp4"):
                        st.session_state.rendered_video_path = p_str
                    elif p_str.endswith(".mp3"):
                        st.session_state.rendered_audio_path = p_str
                        srt_cand = p_str.replace("voice_", "subs_").replace(".mp3", ".srt")
                        if os.path.exists(srt_cand):
                            st.session_state.rendered_srt_path = srt_cand

        if st.session_state.render_message:
            st.success(st.session_state.render_message)

        # In-App Video Playback & Download Cards
        has_video = st.session_state.rendered_video_path and os.path.exists(st.session_state.rendered_video_path)
        has_audio = st.session_state.rendered_audio_path and os.path.exists(st.session_state.rendered_audio_path)

        if has_video:
            st.markdown("##### 📺 Master Video Player")
            st.video(st.session_state.rendered_video_path)
            with open(st.session_state.rendered_video_path, "rb") as vf:
                st.download_button(
                    "⬇️ DOWNLOAD MASTER MP4 VIDEO",
                    data=vf.read(),
                    file_name=Path(st.session_state.rendered_video_path).name,
                    mime="video/mp4",
                    type="primary",
                    use_container_width=True,
                )

        if has_audio or has_video or st.session_state.render_message:
            st.markdown("##### 📦 Production Assets Ready for Download")
            d_col1, d_col2 = st.columns(2)

            if has_audio:
                with d_col1:
                    st.audio(st.session_state.rendered_audio_path)
                    with open(st.session_state.rendered_audio_path, "rb") as af:
                        st.download_button(
                            "⬇️ Download Voiceover Audio (.mp3)",
                            data=af.read(),
                            file_name=Path(st.session_state.rendered_audio_path).name,
                            mime="audio/mp3",
                            use_container_width=True,
                        )

            srt_path = st.session_state.rendered_srt_path or (st.session_state.rendered_audio_path.replace(".mp3", ".srt") if has_audio else "")
            if srt_path and os.path.exists(srt_path):
                with d_col2:
                    with open(srt_path, "rb") as sf:
                        st.download_button(
                            "⬇️ Download Subtitles (.srt)",
                            data=sf.read(),
                            file_name=Path(srt_path).name,
                            mime="text/plain",
                            use_container_width=True,
                        )

            zip_path = OUTPUTS_DIR / "production_asset_bundle.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                if has_video: zf.write(st.session_state.rendered_video_path, arcname=Path(st.session_state.rendered_video_path).name)
                if has_audio: zf.write(st.session_state.rendered_audio_path, arcname=Path(st.session_state.rendered_audio_path).name)
                if srt_path and os.path.exists(srt_path): zf.write(srt_path, arcname=Path(srt_path).name)
                zf.writestr("narration_script.txt", st.session_state.script)

            if zip_path.exists():
                with open(zip_path, "rb") as zf_file:
                    st.download_button(
                        "📦 Download Complete Production Bundle (.zip)",
                        data=zf_file.read(),
                        file_name="studio_production_bundle.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )

    # 6. Packaging & Thumbnail Canvas Dropdown
    with st.expander("🎨 High-CTR Vector Thumbnail & Social Packaging", expanded=False):
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
