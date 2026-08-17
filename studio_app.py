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

AUTO_GEMINI_KEY = get_secure_key("GEMINI_API_KEY") or get_secure_key("GOOGLE_API_KEY") or "AIzaSyCRI7Uu1rpy_oo9r3F8MFgn8vQ1OLGm308"
AUTO_YT_KEY = get_secure_key("YOUTUBE_API_KEY") or AUTO_GEMINI_KEY

# ---------------------------------------------------------
# High-Contrast Obsidian Studio Design System
# ---------------------------------------------------------
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Outfit:wght@600;700;800;900&family=Space+Grotesk:wght@600;700&display=swap');

:root {
  --bg-deep: #080d1a;
  --bg-card: #0f172a;
  --border-card: #334155;
  --text-primary: #ffffff;
  --text-secondary: #cbd5e1;
  --emerald-main: #10b981;
  --emerald-glow: rgba(16, 185, 129, 0.35);
  --cyan-main: #06b6d4;
  --amber-main: #f59e0b;
}

.stApp {
  background-color: var(--bg-deep);
  color: var(--text-primary);
  font-family: 'Plus Jakarta Sans', sans-serif;
}

.block-container {
  max-width: 1540px;
  padding: 1rem 2rem 4rem;
}

h1, h2, h3, h4, h5, h6 {
  font-family: 'Outfit', sans-serif;
  letter-spacing: -0.025em;
  color: #ffffff !important;
  font-weight: 800;
}

[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--bg-card);
  border: 1px solid var(--border-card) !important;
  border-radius: 16px !important;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
  padding: 1.2rem 1.4rem;
  margin-bottom: 0.6rem;
}

.pro-navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--border-card);
  padding: 0.4rem 0 1.2rem;
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

.eyebrow {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.76rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: var(--emerald-main);
  font-weight: 800;
  margin-bottom: 0.65rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.idea-card {
  padding: 0.85rem 1rem;
  border: 1px solid var(--border-card);
  border-radius: 12px;
  background: rgba(30, 41, 59, 0.75);
  margin-bottom: 0.6rem;
  transition: all 0.2s ease;
}

.idea-card:hover {
  border-color: var(--emerald-main);
  background: rgba(16, 185, 129, 0.08);
}

.idea-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.35rem;
}

.idea-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #ffffff;
}

.idea-signal {
  font-size: 0.82rem;
  color: var(--text-secondary);
  margin-top: 0.25rem;
}

.viral-badge {
  font-size: 0.75rem;
  font-weight: 800;
  padding: 0.2rem 0.55rem;
  border-radius: 6px;
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.4);
}

.hook-card {
  padding: 0.75rem 1rem;
  border: 1px solid var(--border-card);
  border-radius: 12px;
  background: rgba(30, 41, 59, 0.75);
  margin-bottom: 0.6rem;
  color: #ffffff;
  font-size: 0.92rem;
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
    st.markdown("### ⚡ AI Studio Engine")

    llm_choice = st.selectbox("AI Intelligence Tier", ["Google Gemini 3.6-Flash (Active)", "OpenAI / Local Ollama", "Demo Sandbox"], index=0)

    gemini_key = AUTO_GEMINI_KEY
    if not gemini_key and "Gemini" in llm_choice:
        gemini_key = st.text_input("Gemini API Key", type="password", help="Enter your Google Gemini API key.")
    elif gemini_key and "Gemini" in llm_choice:
        st.success(f"🔒 **Gemini Connected:** `••••••••{gemini_key[-5:]}`")

    openai_key = get_secure_key("OPENAI_API_KEY")
    if "OpenAI" in llm_choice:
        openai_key = st.text_input("OpenAI Key", value=openai_key, type="password")

    st.markdown("---")
    st.markdown("#### 📡 Market Intelligence APIs")
    yt_key = AUTO_YT_KEY
    if yt_key:
        st.caption(f"🟢 **YouTube Data API Connected:** `••••••••{yt_key[-5:]}`")
    else:
        yt_key = st.text_input("YouTube Data API Key", type="password")

    pexels_key = get_secure_key("PEXELS_API_KEY")
    if not pexels_key:
        pexels_key = st.text_input("Pexels Key (Optional)", type="password", help="Leave blank for built-in high-energy motion graphics engine.")

    st.markdown("---")
    st.markdown("#### 🗂️ Project Library")
    saved_projects = list_saved_projects(OUTPUTS_DIR)
    if saved_projects:
        proj_options = {p.get("project_id", ""): f"{p.get('topic', 'Untitled')[:20]} ({p.get('updated_at', '')[:10]})" for p in saved_projects}
        sel_p = st.selectbox("Saved Drafts", list(proj_options.keys()), format_func=lambda k: proj_options.get(k, k))
        c1, c2 = st.columns(2)
        if c1.button("📂 Load", use_container_width=True):
            loaded = load_project_draft(sel_p, OUTPUTS_DIR)
            if loaded:
                for k, v in loaded.items():
                    st.session_state[k] = v
                st.rerun()
        if c2.button("🗑️ Delete", use_container_width=True):
            delete_project_draft(sel_p, OUTPUTS_DIR)
            st.rerun()

current_llm = get_llm_provider("gemini" if "Gemini" in llm_choice else llm_choice, api_key=gemini_key or openai_key)

# ---------------------------------------------------------
# State Defaults
# ---------------------------------------------------------
if "niche" not in st.session_state:
    st.session_state.niche = "Real Estate"
if "topic" not in st.session_state:
    st.session_state.topic = "I Sent 500 Hand-Written Letters to Zombie Properties (The Shocking Results)"
if "suggested_topics" not in st.session_state:
    st.session_state.suggested_topics = []
if "council_proposals" not in st.session_state:
    st.session_state.council_proposals = []
if "selected_angle_idx" not in st.session_state:
    st.session_state.selected_angle_idx = 0
if "hooks" not in st.session_state:
    st.session_state.hooks = []
if "script" not in st.session_state:
    st.session_state.script = ""
if "tone_preset" not in st.session_state:
    st.session_state.tone_preset = "Alex Hormozi Framework"
if "voice_model" not in st.session_state:
    st.session_state.voice_model = "en-US-JennyNeural-Female"
if "aspect_ratio" not in st.session_state:
    st.session_state.aspect_ratio = "9:16 (Shorts/TikTok/Reels)"
if "video_pacing" not in st.session_state:
    st.session_state.video_pacing = "⚡ Fast (3s Viral Cuts)"
if "visual_theme" not in st.session_state:
    st.session_state.visual_theme = "⚡ Cyberpunk Matrix & Code"
if "subtitle_style" not in st.session_state:
    st.session_state.subtitle_style = "🟡 Hormozi Pop (Gold/Emerald)"
if "competitors" not in st.session_state:
    st.session_state.competitors = []
if "rendered_video_path" not in st.session_state:
    st.session_state.rendered_video_path = ""
if "rendered_audio_path" not in st.session_state:
    st.session_state.rendered_audio_path = ""
if "rendered_srt_path" not in st.session_state:
    st.session_state.rendered_srt_path = ""
if "render_message" not in st.session_state:
    st.session_state.render_message = ""

# ---------------------------------------------------------
# Top Studio Header
# ---------------------------------------------------------
st.markdown(
    '<div class="pro-navbar">'
    '<div class="brand-badge">🎬 SIGNAL STUDIO <span>· PRO</span></div>'
    f'<div class="engine-status-pill">● {current_llm.provider_name.upper()} ACTIVE</div>'
    '</div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 2-Panel Production Creator Workstation
# ---------------------------------------------------------
left_panel, right_panel = st.columns([1.15, 1.1], gap="large")

with left_panel:
    # 1. Step 1: Niche & Topic (AI Brainstormer)
    with st.container(border=True):
        st.markdown('<div class="eyebrow">STEP 01 · Niche & Viral Topic Engine</div>', unsafe_allow_html=True)
        col_n1, col_n2 = st.columns([1.2, 1])
        st.session_state.niche = col_n1.text_input("Enter Your Niche", st.session_state.niche, placeholder="e.g. Fitness, Real Estate, Crypto, AI Tools")

        if col_n2.button("💡 AI Brainstorm 3 Viral Ideas", type="primary", use_container_width=True):
            with st.spinner(f"Querying Google Gemini for viral {st.session_state.niche} angles..."):
                st.session_state.suggested_topics = current_llm.generate_topics(
                    niche=st.session_state.niche,
                    audience="YouTube viewers looking for actionable value",
                    goal="High-retention viral reach",
                )
            st.rerun()

        # Display AI Suggested Topic Cards
        if st.session_state.suggested_topics:
            st.markdown("##### ⚡ Gemini Viral Suggestions (Click to Select):")
            for t_idx, item in enumerate(st.session_state.suggested_topics):
                t_col1, t_col2 = st.columns([4, 1.2])
                with t_col1:
                    st.markdown(
                        f"""<div class="idea-card">
                          <div class="idea-header">
                            <span class="idea-title">{item['topic']}</span>
                            <span class="viral-badge">🔥 {item.get('score', 95)} Viral Score</span>
                          </div>
                          <div class="idea-signal">{item.get('signal', '')}</div>
                        </div>""",
                        unsafe_allow_html=True,
                    )
                with t_col2:
                    if st.button("⚡ Select", key=f"btn_pick_topic_{t_idx}", use_container_width=True):
                        st.session_state.topic = item["topic"]
                        with st.spinner("Generating custom hooks & script with Gemini..."):
                            st.session_state.competitors = fetch_live_youtube_competitors(st.session_state.topic, api_key=yt_key, limit=3)
                            st.session_state.hooks = generate_hook_variations(st.session_state.topic, st.session_state.niche, llm_provider=current_llm)
                            props, win_idx, _ = run_council(st.session_state.topic, st.session_state.niche, llm_provider=current_llm, competitors=st.session_state.competitors)
                            st.session_state.council_proposals = props
                            st.session_state.selected_angle_idx = win_idx
                            chosen = props[win_idx] if props else {}
                            st.session_state.script = make_script(
                                topic=st.session_state.topic,
                                angle=chosen.get("angle", ""),
                                thesis=chosen.get("thesis", ""),
                                hook=chosen.get("hook", ""),
                                niche=st.session_state.niche,
                                tone_preset=st.session_state.tone_preset,
                                llm_provider=current_llm,
                                competitors=st.session_state.competitors,
                            )
                        st.rerun()

        st.session_state.topic = st.text_input("Active Video Topic", st.session_state.topic)

        gen_c1, gen_c2 = st.columns(2)
        if gen_c1.button("🔄 Auto-Run Council & Generate All", type="primary", use_container_width=True):
            with st.spinner("Executing Live Gemini Council, Custom Hooks & Script..."):
                st.session_state.competitors = fetch_live_youtube_competitors(st.session_state.topic, api_key=yt_key, limit=3)
                st.session_state.hooks = generate_hook_variations(st.session_state.topic, st.session_state.niche, llm_provider=current_llm)
                props, win_idx, _ = run_council(st.session_state.topic, st.session_state.niche, llm_provider=current_llm, competitors=st.session_state.competitors)
                st.session_state.council_proposals = props
                st.session_state.selected_angle_idx = win_idx
                chosen = props[win_idx] if props else {}
                st.session_state.script = make_script(
                    topic=st.session_state.topic,
                    angle=chosen.get("angle", ""),
                    thesis=chosen.get("thesis", ""),
                    hook=chosen.get("hook", ""),
                    niche=st.session_state.niche,
                    tone_preset=st.session_state.tone_preset,
                    llm_provider=current_llm,
                    competitors=st.session_state.competitors,
                )
            st.rerun()

        if gen_c2.button("💾 Save Project Draft", use_container_width=True):
            save_project_draft({k: st.session_state[k] for k in ["niche", "topic", "script", "tone_preset", "voice_model", "aspect_ratio", "video_pacing", "subtitle_style", "visual_theme"]}, OUTPUTS_DIR)
            st.success("Project draft saved to local library!")

    # 2. Step 2: 3-Second Viral Hook Lab (Live Gemini Generated)
    with st.container(border=True):
        st.markdown('<div class="eyebrow">STEP 02 · 3-Second Viral Hook Lab (Tailored by Gemini)</div>', unsafe_allow_html=True)
        if not st.session_state.hooks:
            st.session_state.hooks = generate_hook_variations(st.session_state.topic, st.session_state.niche, llm_provider=current_llm)

        for h_i, h in enumerate(st.session_state.hooks[:3]):
            h_c1, h_c2 = st.columns([3.6, 1.1])
            with h_c1:
                st.markdown(
                    f"""<div class="hook-card">
                      <div class="hook-meta">
                        <span class="hook-tag">[{h['archetype']}] {h['tag']}</span>
                        <span class="viral-badge">🔥 {h['hold_rate']}% Retention</span>
                      </div>
                      <div>"{h['hook']}"</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
            with h_c2:
                if st.button("⚡ Apply Hook", key=f"btn_hook_{h_i}", use_container_width=True):
                    st.session_state.script = replace_script_hook(st.session_state.script, h["hook"])
                    st.success("Hook inserted into script!")
                    st.rerun()

    # 3. Step 3: Script Narration & Tone Presets
    with st.container(border=True):
        st.markdown('<div class="eyebrow">STEP 03 · Script Narration & Frameworks</div>', unsafe_allow_html=True)

        s_t1, s_t2 = st.columns([1.5, 1])
        tone_opts = ["Alex Hormozi Framework", "Veritasium Investigative Essay", "Viral Shorts / Reels", "Balanced Editorial"]
        st.session_state.tone_preset = s_t1.selectbox("Creator Tone Framework", tone_opts, index=tone_opts.index(st.session_state.tone_preset) if st.session_state.tone_preset in tone_opts else 0)

        if s_t2.button("✍️ Re-Generate Script (Gemini)", use_container_width=True):
            with st.spinner("Drafting fresh script with selected tone framework..."):
                st.session_state.script = make_script(
                    topic=st.session_state.topic,
                    angle="Core Differentiated Angle",
                    niche=st.session_state.niche,
                    tone_preset=st.session_state.tone_preset,
                    llm_provider=current_llm,
                    competitors=st.session_state.competitors,
                )
            st.rerun()

        if not st.session_state.script:
            st.session_state.script = make_script(
                topic=st.session_state.topic,
                angle="Lived Case Study",
                niche=st.session_state.niche,
                tone_preset=st.session_state.tone_preset,
                llm_provider=current_llm,
            )

        ret_audit = audit_script_retention(st.session_state.script)
        words = len(st.session_state.script.split())
        est_sec = round(words / 2.3)
        ret_score = ret_audit.get("score", 88)

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

        st.session_state.script = st.text_area("Narration Script (Editable)", st.session_state.script, height=210, label_visibility="collapsed")

with right_panel:
    # 4. Step 4: Multi-Format Video Customization & Simulator
    with st.container(border=True):
        st.markdown('<div class="eyebrow">STEP 04 · Video Style & Visual Theme Customizer</div>', unsafe_allow_html=True)
        vf_1, vf_2 = st.columns(2)

        aspect_opts = ["9:16 (Shorts/TikTok/Reels)", "16:9 (YouTube Widescreen)", "1:1 (Square Feed)"]
        st.session_state.aspect_ratio = vf_1.selectbox("Format / Aspect Ratio", aspect_opts, index=aspect_opts.index(st.session_state.aspect_ratio) if st.session_state.aspect_ratio in aspect_opts else 0)

        theme_opts = [
            "⚡ Cyberpunk Matrix & Code",
            "🏙️ Neon City Hyperlapse & Speed",
            "💻 Modern Creator Desk & Workflow",
            "📈 Crypto & Financial Stock Charts",
            "🌌 Cinematic Space & Solar Flare",
            "🎬 Abstract Kinetic Motion",
        ]
        st.session_state.visual_theme = vf_2.selectbox("Master Video Background Theme", theme_opts, index=theme_opts.index(st.session_state.visual_theme) if st.session_state.visual_theme in theme_opts else 0)

        vf_3, vf_4 = st.columns(2)
        pacing_opts = ["⚡ Fast (3s Viral Cuts)", "🎬 Standard (5s Flow)", "📽️ Cinematic (8s Deep Dive)"]
        st.session_state.video_pacing = vf_3.selectbox("Scene Cut Velocity", pacing_opts, index=pacing_opts.index(st.session_state.video_pacing) if st.session_state.video_pacing in pacing_opts else 0)

        sub_opts = ["🟡 Hormozi Pop (Gold/Emerald)", "🔴 MrBeast Impact (Bold Red)", "🔵 Cyber Cyan", "⚪ Clean Minimalist"]
        st.session_state.subtitle_style = vf_4.selectbox("Subtitle Animation Style", sub_opts, index=sub_opts.index(st.session_state.subtitle_style) if st.session_state.subtitle_style in sub_opts else 0)

    # 4.5 Live Interactive Video Simulator
    target_clip_sec = 3 if "3s" in st.session_state.video_pacing else 8 if "8s" in st.session_state.video_pacing else 5
    scenes = segment_script_into_scenes(st.session_state.script, target_clip_duration_sec=target_clip_sec)

    with st.container(border=True):
        st.markdown(f'<div class="eyebrow">04.5 · Live Simulator ({st.session_state.visual_theme})</div>', unsafe_allow_html=True)

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
        st.markdown('<div class="eyebrow">05 · Master Video Render & Loud Audio Export Hub</div>', unsafe_allow_html=True)

        render_progress = st.progress(0, text="Ready for instant rendering.")

        if st.button("🎬 RENDER MASTER PRODUCTION MP4 VIDEO", type="primary", use_container_width=True):
            def on_progress(text: str, pct: float):
                render_progress.progress(int(pct * 100), text=text)

            with st.spinner("Synthesizing voice audio & assembling multi-scene master video..."):
                settings = {
                    "voice_name": st.session_state.voice_model,
                    "voice_rate": 1.0,
                    "video_aspect": st.session_state.aspect_ratio.split()[0],
                    "video_clip_duration": target_clip_sec,
                    "visual_theme": st.session_state.visual_theme,
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
                        # Also track the generated mp3
                        audio_cand = OUTPUTS_DIR / "audio"
                        if audio_cand.exists():
                            for mp in audio_cand.glob("*.mp3"):
                                if mp.stat().st_size > 1000:
                                    st.session_state.rendered_audio_path = str(mp.resolve())
                                    break
                    elif p_str.endswith(".mp3"):
                        st.session_state.rendered_audio_path = p_str

        if st.session_state.render_message:
            st.success(st.session_state.render_message)

        # In-App Video Playback & Download Cards
        has_video = st.session_state.rendered_video_path and os.path.exists(st.session_state.rendered_video_path)
        has_audio = st.session_state.rendered_audio_path and os.path.exists(st.session_state.rendered_audio_path)

        if has_video:
            st.markdown("##### 📺 Master Video Player (With Spoken Voice Audio)")
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
            st.markdown("##### 🔊 Standalone Audio & Production Assets")
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
