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
    page_title="Signal Studio · Embedded Video Engine",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
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

.competitor-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  background: #f8fafc;
  border: 1px solid var(--line);
  border-radius: 8px;
  margin-bottom: 0.5rem;
}

.competitor-thumb {
  width: 90px;
  height: 52px;
  border-radius: 6px;
  object-fit: cover;
}

.competitor-info {
  font-size: 0.82rem;
  line-height: 1.25;
}

.competitor-title {
  font-weight: 700;
  color: #0f172a;
}

.competitor-meta {
  color: #64748b;
  font-size: 0.75rem;
}

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
# Sidebar: Settings & Live API Keys
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Engine & API Connections")
    llm_choice = st.selectbox("AI Engine", ["Google Gemini (Recommended)", "OpenAI / Local Ollama", "Demo (Zero Keys)"], index=0)
    gemini_key = st.text_input("Gemini API Key", value=os.getenv("GEMINI_API_KEY", ""), type="password", help="Enables live Google Gemini 2.5 flash reasoning.") if "Gemini" in llm_choice else ""
    openai_key = st.text_input("OpenAI Key", value=os.getenv("OPENAI_API_KEY", ""), type="password") if "OpenAI" in llm_choice else ""

    st.markdown("#### 📡 Market Intelligence APIs")
    yt_api_key = st.text_input("YouTube Data API v3 Key (Optional)", value=os.getenv("YOUTUBE_API_KEY", ""), type="password", help="Fetches live competitor view counts, ranking titles, and thumbnails directly from YouTube.")
    google_search_key = st.text_input("Google Search API Key (Optional)", value=os.getenv("GOOGLE_SEARCH_KEY", ""), type="password", help="Fetches live primary citations.")
    google_cx = st.text_input("Google CSE ID (Optional)", value=os.getenv("GOOGLE_SEARCH_CX", ""), type="password") if google_search_key else ""
    pexels_key = st.text_input("Pexels API Key (Optional)", value=os.getenv("PEXELS_API_KEY", ""), type="password", help="Custom Pexels stock video search key.")

    st.markdown("---")
    st.markdown("### 🗂️ Saved Project Library")
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
# Top Navigation Bar
# ---------------------------------------------------------
st.markdown(
    '<div class="top-nav">'
    '<div class="brand-title"><b>🎬 SIGNAL STUDIO</b> <span>· YouTube Market Intel & Video Engine</span></div>'
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
        st.markdown('<div class="eyebrow">01 · Topic & Live Market Intel</div>', unsafe_allow_html=True)
        col_a, col_b = st.columns([1, 1.5])
        st.session_state.niche = col_a.text_input("Niche", st.session_state.niche)
        st.session_state.topic = col_b.text_input("Video Topic", st.session_state.topic)

        gen_c1, gen_c2 = st.columns(2)
        if gen_c1.button("✨ Auto-Generate Storyboard", type="primary", use_container_width=True):
            with st.spinner("Fetching live YouTube competitor data & AI Council..."):
                # Fetch live YouTube competitor references
                st.session_state.competitors = fetch_live_youtube_competitors(
                    query=st.session_state.topic,
                    api_key=yt_api_key,
                    limit=3,
                )
                citations = fetch_research_pack(
                    topic=st.session_state.topic,
                    google_api_key=google_search_key,
                    google_cx=google_cx,
                )

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

        if gen_c2.button("💾 Save Draft", use_container_width=True):
            save_project_draft({k: st.session_state[k] for k in defaults.keys()}, OUTPUTS_DIR)
            st.success("Draft saved!")

    # 1.5 Live YouTube Competitor Cards
    if st.session_state.competitors:
        with st.container(border=True):
            st.markdown('<div class="eyebrow">📡 Live YouTube Competitor References</div>', unsafe_allow_html=True)
            st.caption("The AI has analyzed these ranking videos to formulate a differentiated, contrarian angle:")
            for comp in st.session_state.competitors[:3]:
                st.markdown(
                    f"""<div class="competitor-card">
                      <img src="{comp.get('thumbnail')}" class="competitor-thumb" />
                      <div class="competitor-info">
                        <div class="competitor-title">{comp.get('title')}</div>
                        <div class="competitor-meta">📺 {comp.get('channel')} · 🔥 {comp.get('views')} · <a href="{comp.get('url')}" target="_blank">Watch Video ↗</a></div>
                      </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

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
            with st.spinner("Rewriting with selected tone & competitor intelligence..."):
                citations = fetch_research_pack(st.session_state.topic, google_api_key=google_search_key, google_cx=google_cx)
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

        # Download & Playback Section
        has_video = st.session_state.rendered_video_path and os.path.exists(st.session_state.rendered_video_path)
        has_audio = st.session_state.rendered_audio_path and os.path.exists(st.session_state.rendered_audio_path)

        if has_video:
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

        if has_audio or has_video or st.session_state.render_message:
            st.markdown("##### 📦 Generated Media Assets Ready for Download")
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

            # Subtitle download
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

            # Zip Complete Production Bundle
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
                        file_name="studio_video_bundle.zip",
                        mime="application/zip",
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
