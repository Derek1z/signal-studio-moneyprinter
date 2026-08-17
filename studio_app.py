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
# Secure Key Resolver (Secrets -> Env -> Fallback)
# ---------------------------------------------------------
def get_secure_key(name: str) -> str:
    """Retrieve sensitive API credentials safely from Streamlit secrets or OS environment."""
    if hasattr(st, "secrets") and name in st.secrets:
        return str(st.secrets[name]).strip()
    return os.getenv(name, "").strip()

AUTO_GEMINI_KEY = get_secure_key("GEMINI_API_KEY") or get_secure_key("GOOGLE_API_KEY")
AUTO_YT_KEY = get_secure_key("YOUTUBE_API_KEY") or AUTO_GEMINI_KEY

# ---------------------------------------------------------
# High-End Obsidian Creator Studio Design System
# ---------------------------------------------------------
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400;1,700&family=Outfit:wght@600;700;800;900&family=Space+Grotesk:wght@600;700&display=swap');

:root {
  --bg-deep: #060911;
  --bg-card: #0d1322;
  --bg-card-hover: #131b2e;
  --bg-glass: rgba(13, 19, 34, 0.75);
  --border-subtle: #1e293b;
  --border-glow: rgba(16, 185, 129, 0.35);
  --text-primary: #f8fafc;
  --text-muted: #94a3b8;
  --text-dim: #64748b;
  --emerald-primary: #10b981;
  --emerald-hover: #059669;
  --emerald-glow: rgba(16, 185, 129, 0.25);
  --cyan-accent: #06b6d4;
  --amber-warning: #f59e0b;
}

/* Global App Shell */
.stApp {
  background-color: var(--bg-deep);
  color: var(--text-primary);
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.block-container {
  max-width: 1480px;
  padding: 1.2rem 2rem 4rem;
}

h1, h2, h3, h4, h5, h6 {
  font-family: 'Outfit', sans-serif;
  letter-spacing: -0.025em;
  color: var(--text-primary);
}

/* Cards & Containers */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle) !important;
  border-radius: 16px !important;
  box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(12px);
  padding: 1rem 1.25rem;
}

/* Top Studio Navigation Bar */
.pro-navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-subtle);
  padding: 0.6rem 0 1.2rem;
  margin-bottom: 1.5rem;
}

.brand-badge {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-family: 'Outfit', sans-serif;
  font-size: 1.35rem;
  font-weight: 900;
  letter-spacing: -0.03em;
  color: #ffffff;
}

.brand-badge span {
  color: var(--emerald-primary);
  text-shadow: 0 0 12px var(--emerald-glow);
}

.engine-status-pill {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  font-weight: 800;
  padding: 0.4rem 0.9rem;
  border-radius: 99px;
  background: rgba(16, 185, 129, 0.12);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.35);
  box-shadow: 0 0 15px rgba(16, 185, 129, 0.15);
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.engine-status-pill::before {
  content: "";
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 10px #10b981;
  animation: pulseDot 2s infinite ease-in-out;
}

@keyframes pulseDot {
  0% { transform: scale(0.9); opacity: 0.6; }
  50% { transform: scale(1.3); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.6; }
}

/* Eyebrows & Section Headers */
.eyebrow {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: var(--emerald-primary);
  font-weight: 700;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

/* Viral Hook Card */
.hook-card {
  padding: 0.75rem 1rem;
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.6);
  margin-bottom: 0.6rem;
  font-size: 0.88rem;
  line-height: 1.45;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.hook-card:hover {
  border-color: var(--emerald-primary);
  background: rgba(16, 185, 129, 0.05);
  transform: translateX(3px);
}

.hook-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.35rem;
}

.hook-tag {
  font-size: 0.72rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--cyan-accent);
}

.hold-rate-badge {
  font-size: 0.72rem;
  font-weight: 800;
  padding: 0.15rem 0.5rem;
  border-radius: 6px;
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.3);
}

/* Competitor Radar Card */
.competitor-row {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 0.65rem 0.85rem;
  background: rgba(15, 23, 42, 0.75);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  margin-bottom: 0.6rem;
  transition: all 0.2s ease;
}

.competitor-row:hover {
  border-color: rgba(255, 255, 255, 0.2);
  background: rgba(19, 27, 46, 0.9);
}

.comp-img {
  width: 96px;
  height: 54px;
  border-radius: 8px;
  object-fit: cover;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.comp-content {
  flex: 1;
  min-width: 0;
}

.comp-title {
  font-size: 0.84rem;
  font-weight: 700;
  color: #f1f5f9;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.comp-meta {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 0.2rem;
}

.comp-link {
  color: var(--cyan-accent);
  text-decoration: none;
  font-weight: 600;
}

/* Retention Gauge Meter */
.retention-bar-wrapper {
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 0.85rem 1.1rem;
  margin-bottom: 0.85rem;
}

.retention-stats {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.82rem;
  font-weight: 700;
  margin-bottom: 0.4rem;
}

.retention-fill-track {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.08);
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
  font-size: 0.9rem;
  min-height: 2.75rem;
  transition: all 0.2s ease;
  border: 1px solid var(--border-subtle);
  background: #131c30;
  color: #f8fafc;
}

.stButton > button:hover {
  background: #1e293b;
  border-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
}

.stButton > button[kind="primary"] {
  background: var(--emerald-primary);
  border-color: var(--emerald-primary);
  color: #04100c;
  font-weight: 800;
  box-shadow: 0 4px 18px rgba(16, 185, 129, 0.35);
}

.stButton > button[kind="primary"]:hover {
  background: #34d399;
  border-color: #34d399;
  box-shadow: 0 6px 24px rgba(16, 185, 129, 0.5);
  transform: translateY(-2px);
}

/* Text Inputs and Selects */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
  background-color: #090e1a !important;
  border-color: var(--border-subtle) !important;
  color: #f8fafc !important;
  border-radius: 10px !important;
}

.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: var(--emerald-primary) !important;
  box-shadow: 0 0 0 1px var(--emerald-primary) !important;
}
</style>""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar: Settings & Live Credentials
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚡ Studio Control Engine")

    llm_choice = st.selectbox("AI Intelligence Tier", ["Google Gemini 2.5 (Active)", "OpenAI / Local Ollama", "Demo Sandbox"], index=0)

    # Automatically resolve Gemini key from secure vault
    gemini_key = AUTO_GEMINI_KEY
    if not gemini_key and "Gemini" in llm_choice:
        gemini_key = st.text_input("Gemini API Key", type="password", help="Enter your Google Gemini API key.")
    elif gemini_key and "Gemini" in llm_choice:
        st.caption(f"🔒 **Gemini Key Active:** `••••••••{gemini_key[-5:]}`")

    openai_key = get_secure_key("OPENAI_API_KEY")
    if "OpenAI" in llm_choice:
        openai_key = st.text_input("OpenAI Key", value=openai_key, type="password")

    st.markdown("---")
    st.markdown("#### 📡 Live Intelligence Channels")
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
# State Initialization
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
    # 1. Brief & Live Market Radar
    with st.container(border=True):
        st.markdown('<div class="eyebrow">01 · Topic Brief & Live Market Radar</div>', unsafe_allow_html=True)
        col_a, col_b = st.columns([1, 1.6])
        st.session_state.niche = col_a.text_input("Creator Niche", st.session_state.niche)
        st.session_state.topic = col_b.text_input("Core Video Topic", st.session_state.topic)

        gen_c1, gen_c2 = st.columns(2)
        if gen_c1.button("✨ Auto-Generate Full Storyboard", type="primary", use_container_width=True):
            with st.spinner("Analyzing live YouTube competitor radar & executing AI Council..."):
                # Fetch live YouTube competitor benchmarks
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

    # 1.5 Live Competitor Benchmarks Card
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
                        <div class="comp-meta">📺 {comp.get('channel')} · 🔥 {comp.get('views')} · <a href="{comp.get('url')}" target="_blank" class="comp-link">Watch on YouTube ↗</a></div>
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

    # 3. Narration Script & Tone Presets
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

        # Real-time Retention Audit
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
        st.components.v1.html(sim_html, height=430, scrolling=False)

    # 5. Native In-House MP4 Video Rendering Engine
    with st.container(border=True):
        st.markdown('<div class="eyebrow">05 · In-House Video Render & Export Hub</div>', unsafe_allow_html=True)

        r1, r2 = st.columns(2)
        st.session_state.voice_model = r1.selectbox("Neural Voice", list(AVAILABLE_VOICES.keys()), index=0)
        st.session_state.aspect_ratio = r2.selectbox("Video Format", ["16:9 (Widescreen)", "9:16 (Shorts/Reels)"])

        render_progress = st.progress(0, text="Ready for instant rendering.")

        if st.button("🎬 RENDER PRODUCTION MP4 VIDEO", type="primary", use_container_width=True):
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
