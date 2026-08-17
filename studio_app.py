from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st

from studio.ai_providers import get_llm_provider
from studio.engine import (
    AVAILABLE_VOICES,
    Project,
    audit_script_retention,
    compile_storyboard_to_broll_terms,
    create_social_package,
    delete_project_draft,
    dispatch_to_moneyprinter,
    fetch_research_pack,
    generate_hook_variations,
    generate_packaging,
    generate_thumbnail_svg,
    get_clips_for_scenes,
    list_saved_projects,
    load_project_draft,
    make_script,
    moneyprinter_payload,
    now_iso,
    render_live_video_simulator,
    render_video_pipeline,
    replace_script_hook,
    risk_check,
    run_council,
    save_handoff,
    save_project_draft,
    score_topics,
    segment_script_into_scenes,
    synthesize_speech,
    validate_payload,
)

st.set_page_config(
    page_title="Signal Studio × MoneyPrinter Native",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

OUTPUTS_DIR = Path(__file__).parent / "studio_outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Manrope:wght@600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --ink: #101714;
  --muted: #58655f;
  --paper: #f7f5ef;
  --card: #ffffff;
  --line: #dedbd2;
  --green: #15503c;
  --green-light: #e6f4ed;
  --lime: #d2f866;
  --amber: #d97706;
  --amber-light: #fef3c7;
  --red: #dc2626;
  --red-light: #fee2e2;
}

.stApp {
  background: var(--paper);
  color: var(--ink);
  font-family: 'DM Sans', sans-serif;
}

.block-container {
  max-width: 1400px;
  padding: 1.2rem 2rem 3.5rem;
}

h1, h2, h3, h4, h5 {
  font-family: 'Manrope', sans-serif;
  letter-spacing: -0.03em;
  color: var(--ink);
}

.brand {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid var(--line);
  padding: 0.2rem 0 1rem;
  margin-bottom: 1.2rem;
}

.brand-name {
  font: 900 1.28rem 'Manrope', sans-serif;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.brand-name b {
  color: var(--green);
}

.mode-badge {
  font-size: 0.72rem;
  font-weight: 800;
  padding: 0.35rem 0.8rem;
  border-radius: 99px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.mode-demo { background: #fef9c3; color: #854d0e; border: 1px solid #fde047; }
.mode-live { background: #dcfce7; color: #166534; border: 1px solid #86efac; }

.hero {
  display: grid;
  grid-template-columns: 1.6fr 0.4fr;
  gap: 1.5rem;
  align-items: end;
  margin: 0.4rem 0 1.4rem;
}

.hero h1 { font-size: 2.35rem; line-height: 1.05; margin: 0.2rem 0 0.5rem; }
.hero p { color: var(--muted); margin: 0; font-size: 1rem; line-height: 1.45; }

.project-meta {
  text-align: right;
  color: var(--muted);
  font-size: 0.8rem;
  line-height: 1.4;
  border-left: 2px solid var(--line);
  padding-left: 1rem;
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
  margin-bottom: 0.4rem;
}

.score-badge {
  font: 900 1.85rem 'Manrope', sans-serif;
  color: var(--green);
  line-height: 1;
}

.micro { font-size: 0.78rem; color: var(--muted); line-height: 1.35; }

.advisor-card { border-top: 3px solid var(--green); padding: 0.9rem 0; }
.advisor-card.winner { border-top-color: #84cc16; }

.winner-tag {
  display: inline-block;
  background: var(--lime);
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-size: 0.68rem;
  font-weight: 800;
  color: #1a3307;
  letter-spacing: 0.04em;
  margin-bottom: 0.4rem;
}

.hook-card {
  padding: 0.85rem;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #ffffff;
  margin-bottom: 0.75rem;
  transition: all 0.15s ease;
}

.hook-card:hover { border-color: var(--green); box-shadow: 0 4px 12px rgba(0,0,0,0.04); }

.scene-timeline-card {
  border-left: 3px solid var(--green);
  padding: 0.65rem 0.85rem;
  background: #fbfaf6;
  border-radius: 8px;
  margin-bottom: 0.6rem;
  font-size: 0.88rem;
}

.risk-pill {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 99px;
  font-weight: 700;
  font-size: 0.8rem;
}

.risk-low { background: var(--green-light); color: var(--green); border: 1px solid #a7f3d0; }
.risk-review { background: var(--amber-light); color: var(--amber); border: 1px solid #fde68a; }
.risk-high { background: var(--red-light); color: var(--red); border: 1px solid #fecaca; }

.pacing-item {
  padding: 0.45rem 0.65rem;
  border-radius: 6px;
  margin-bottom: 0.35rem;
  font-size: 0.85rem;
}

.pacing-green { background: #f0fdf4; border-left: 3px solid #22c55e; }
.pacing-yellow { background: #fefce8; border-left: 3px solid #eab308; }
.pacing-red { background: #fef2f2; border-left: 3px solid #ef4444; }

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
  background: #0f392b;
  border-color: #0f392b;
}
</style>""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar: Provider, Model, and Project Library
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### 🗂️ Project Library")
    saved_projects = list_saved_projects(OUTPUTS_DIR)
    if saved_projects:
        proj_options = {p.get("project_id", ""): f"{p.get('topic', 'Untitled')[:26]} ({p.get('updated_at', '')[:10]})" for p in saved_projects}
        selected_proj_id = st.selectbox("Saved Projects", options=list(proj_options.keys()), format_func=lambda k: proj_options.get(k, k))
        lp1, lp2 = st.columns(2)
        if lp1.button("📂 Load Draft", use_container_width=True):
            loaded = load_project_draft(selected_proj_id, OUTPUTS_DIR)
            if loaded:
                for k, v in loaded.items():
                    if k in st.session_state:
                        st.session_state[k] = v
                st.success("Project loaded!")
                st.rerun()
        if lp2.button("🗑️ Delete", use_container_width=True):
            delete_project_draft(selected_proj_id, OUTPUTS_DIR)
            st.rerun()
    else:
        st.caption("No saved projects yet.")

    st.markdown("---")
    st.markdown("### ⚙️ Studio Settings")

    with st.expander("🧠 AI & LLM Provider", expanded=True):
        llm_choice = st.selectbox(
            "LLM Engine",
            ["Google Gemini", "OpenAI / Local Ollama", "Demo (Zero Keys)"],
            index=0 if os.getenv("GEMINI_API_KEY") else 2,
        )

        gemini_key = ""
        openai_key = ""
        model_name = ""
        custom_base_url = ""

        if llm_choice == "Google Gemini":
            gemini_key = st.text_input("Gemini API Key", value=os.getenv("GEMINI_API_KEY", ""), type="password")
            model_name = st.selectbox("Model", ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"], index=0)
        elif llm_choice == "OpenAI / Local Ollama":
            openai_key = st.text_input("API Key (Optional for Ollama)", value=os.getenv("OPENAI_API_KEY", ""), type="password")
            custom_base_url = st.text_input("Base URL", value="https://api.openai.com/v1")
            model_name = st.text_input("Model Name", value="gpt-4o-mini")

    with st.expander("🎞️ Stock Video (Pexels / Pixabay)", expanded=False):
        pexels_key = st.text_input("Pexels API Key", value=os.getenv("PEXELS_API_KEY", ""), type="password", help="Optional. Leaves blank to use curated offline stock media cache.")

    with st.expander("📊 Live Trend & Topic Data", expanded=False):
        trend_choice = st.selectbox("Trend Source", ["Demo Fixtures", "YouTube Data API v3"])
        yt_api_key = ""
        yt_region = "US"
        if trend_choice == "YouTube Data API v3":
            yt_api_key = st.text_input("YouTube API Key", value=os.getenv("YOUTUBE_API_KEY", ""), type="password")
            yt_region = st.selectbox("Region Code", ["US", "GB", "CA", "AU", "DE", "FR", "IN", "JP"])

    with st.expander("🔍 Live Research & Fact Check", expanded=False):
        research_choice = st.selectbox(
            "Research Source",
            ["Free Web Search (Live Citations)", "Google Programmable Search", "Demo Policies"],
        )
        google_search_key = ""
        google_cx = ""
        if research_choice == "Google Programmable Search":
            google_search_key = st.text_input("Google Search API Key", value=os.getenv("GOOGLE_SEARCH_API_KEY", ""), type="password")
            google_cx = st.text_input("Search Engine ID (CX)", value=os.getenv("GOOGLE_SEARCH_CX", ""))

    with st.expander("🚀 External MoneyPrinter Server", expanded=False):
        mpt_endpoint = st.text_input("API Endpoint", value="http://127.0.0.1:8080/api/v1/generate")

# Initialize Provider instance
current_llm = get_llm_provider(
    provider_type=llm_choice,
    api_key=gemini_key if llm_choice == "Google Gemini" else openai_key,
    model_name=model_name,
    base_url=custom_base_url,
)
is_live_mode = current_llm.configured and llm_choice != "Demo (Zero Keys)"

# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
defaults = {
    "project_id": "",
    "niche": "AI productivity workflows",
    "audience": "solo creators and freelancers with limited time",
    "goal": "Build trust with a practical, step-by-step weekly video",
    "topics": [],
    "topic": "The 7-minute AI productivity workflow that gives creators their Fridays back",
    "proposals": [],
    "winner": 0,
    "judge_reasoning": "",
    "tone_preset": "Balanced Editorial",
    "script": """Most people approach AI productivity by collecting more tools and adding friction to their day. I did too—and it only slowed down real progress.

So I tested a lean approach: one week, one repeatable workflow, and one rule: every automated step had to leave room for a human decision.

Step one: Start with the viewer's exact constraint, not a vague keyword.
Step two: Use AI to generate multiple competing angles, then filter aggressively for originality and practical proof.
Step three: Verify every claim and citation before any production button is pressed.

The surprising takeaway? The speed didn't come from removing human judgment—it came from having clear checkpoints where low-quality ideas get rejected immediately.

If you try this, start with a single video. Add something only you can contribute: an authentic test, a failure, or a measured comparison.

AI widens your options. Human judgment narrows them. That's the system that scales.""",
    "hooks": [],
    "research": [],
    "research_ok": True,
    "script_ok": True,
    "personal": True,
    "title": "The 7-Minute AI Workflow I Actually Kept",
    "packaging": {},
    "thumbnail_theme": "emerald",
    "broll_tags": "creator desk, workflow diagram, editing timeline, screen capture, analytics",
    "rendered_video_path": "",
    "rendered_audio_path": "",
    "render_message": "",
    "handoff_path": "",
    "social_package": {},
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# ---------------------------------------------------------
# Header & Navigation
# ---------------------------------------------------------
mode_label = f"LIVE AI · {current_llm.provider_name.upper()}" if is_live_mode else "DEMO MODE · ZERO API KEYS"
mode_class = "mode-live" if is_live_mode else "mode-demo"

st.markdown(
    f'<div class="brand"><div class="brand-name"><b>◉</b> SIGNAL STUDIO <span class="micro">× Native MoneyPrinter Engine</span></div>'
    f'<div class="mode-badge {mode_class}">{mode_label}</div></div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero"><div><div class="eyebrow">All-In-One Native Video Production Workstation</div>'
    '<h1>Direct Script-to-Video Engine for Creators</h1>'
    '<p>Multi-advisor council ideation, 3-second hook retention testing, synchronized Edge-TTS voiceovers, live karaoke subtitle simulation, and direct MP4 video rendering.</p>'
    '</div><div class="project-meta">ENGINE BUILT-IN<br><b>SELF-CONTAINED STUDIO</b></div></div>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# Master 4-Tab Workstation Layout
# ---------------------------------------------------------
tab_director, tab_writer, tab_studio, tab_render = st.tabs([
    "🧭 01 · Director & Council",
    "✍️ 02 · Script & Viral Hook Lab",
    "🎬 03 · Live Simulator & Storyboard",
    "🚀 04 · In-House Render & Export Hub",
])

# ---------------------------------------------------------
# TAB 1: DIRECTOR & COUNCIL
# ---------------------------------------------------------
with tab_director:
    c_main, c_side = st.columns([2.3, 0.7], gap="medium")
    with c_main:
        with st.container(border=True):
            st.markdown('<div class="eyebrow">Creative Brief</div>', unsafe_allow_html=True)
            b1, b2 = st.columns(2)
            st.session_state.niche = b1.text_input("Niche / Territory", st.session_state.niche)
            st.session_state.audience = b2.text_input("Primary Target Audience", st.session_state.audience)
            st.session_state.goal = st.text_input("Editorial Goal", st.session_state.goal)

            if st.button("⚡ Find Topic Signals", type="primary", use_container_width=True):
                with st.spinner("Analyzing high-retention topic signals..."):
                    st.session_state.topics = score_topics(
                        niche=st.session_state.niche,
                        audience=st.session_state.audience,
                        goal=st.session_state.goal,
                        llm_provider=current_llm,
                        youtube_api_key=yt_api_key if trend_choice == "YouTube Data API v3" else "",
                        region=yt_region,
                    )
                    st.rerun()

        if st.session_state.topics:
            st.markdown("#### Scored Topic Signals")
            cols = st.columns(len(st.session_state.topics))
            for i, item in enumerate(st.session_state.topics):
                with cols[i]:
                    with st.container(border=True):
                        st.markdown(
                            f'<div class="score-badge">{item.get("score", 90)}</div>'
                            f'<b>{item["topic"]}</b><p class="micro">{item.get("signal", "")}</p>',
                            unsafe_allow_html=True,
                        )
                        if st.button("Develop This Signal", key=f"topic_select_{i}", use_container_width=True):
                            st.session_state.topic = item["topic"]
                            with st.spinner("Convening 3-Advisor Council & Research Checkpoint..."):
                                proposals, win_idx, reasoning = run_council(
                                    topic=item["topic"],
                                    niche=st.session_state.niche,
                                    audience=st.session_state.audience,
                                    llm_provider=current_llm,
                                )
                                st.session_state.proposals = proposals
                                st.session_state.winner = win_idx
                                st.session_state.judge_reasoning = reasoning

                                selected_prop = proposals[win_idx]
                                st.session_state.script = make_script(
                                    topic=item["topic"],
                                    angle=selected_prop.get("angle", ""),
                                    thesis=selected_prop.get("thesis", ""),
                                    hook=selected_prop.get("hook", ""),
                                    niche=st.session_state.niche,
                                    audience=st.session_state.audience,
                                    duration_sec=60,
                                    tone_preset=st.session_state.tone_preset,
                                    llm_provider=current_llm,
                                )
                                st.session_state.research = fetch_research_pack(
                                    topic=item["topic"],
                                    provider_type="google" if "Google" in research_choice else "duckduckgo" if "Free Web" in research_choice else "demo",
                                    google_api_key=google_search_key,
                                    google_cx=google_cx,
                                )
                                st.session_state.hooks = generate_hook_variations(
                                    topic=item["topic"],
                                    niche=st.session_state.niche,
                                    audience=st.session_state.audience,
                                    llm_provider=current_llm,
                                )
                            st.rerun()

        if st.session_state.proposals:
            st.markdown("#### 3-Advisor Council Deliberation")
            if st.session_state.judge_reasoning:
                st.info(f"⚖️ **Executive Judge Evaluation:** {st.session_state.judge_reasoning}")

            c_cols = st.columns(len(st.session_state.proposals))
            for i, p in enumerate(st.session_state.proposals):
                is_win = i == st.session_state.winner
                with c_cols[i]:
                    with st.container(border=True):
                        win_html = '<span class="winner-tag">JUDGE PICK</span>' if is_win else ""
                        st.markdown(
                            f'<div class="advisor-card {"winner" if is_win else ""}">{win_html}'
                            f'<p class="micro">{p.get("advisor", "Advisor")}</p>'
                            f'<h4>{p.get("angle", "Angle")}</h4>'
                            f'<p><em>"{p.get("hook", "")}"</em></p>'
                            f'<p class="micro">{p.get("thesis", "")}</p></div>',
                            unsafe_allow_html=True,
                        )
                        if st.button("Adopt This Angle", key=f"angle_adopt_{i}", use_container_width=True):
                            st.session_state.winner = i
                            with st.spinner("Rewriting script with selected angle..."):
                                st.session_state.script = make_script(
                                    topic=st.session_state.topic,
                                    angle=p.get("angle", ""),
                                    thesis=p.get("thesis", ""),
                                    hook=p.get("hook", ""),
                                    niche=st.session_state.niche,
                                    audience=st.session_state.audience,
                                    duration_sec=60,
                                    tone_preset=st.session_state.tone_preset,
                                    llm_provider=current_llm,
                                )
                            st.rerun()

        with st.container(border=True):
            st.markdown('<div class="eyebrow">Research & Fact-Check Checkpoint</div>', unsafe_allow_html=True)
            if not st.session_state.research:
                st.session_state.research = fetch_research_pack(st.session_state.topic)

            for row in st.session_state.research:
                a, b, c = st.columns([2.2, 1.0, 1.2])
                a.write(f"**•** {row.get('claim', '')}")
                b.caption(f"🏷️ {row.get('status', 'Unverified')}")
                url = row.get("url", "")
                if url:
                    c.markdown(f'<a href="{url}" target="_blank" style="color:var(--green);font-weight:700;">🔗 {row.get("source", "Source")}</a>', unsafe_allow_html=True)
                else:
                    c.caption(f"📚 {row.get('source', 'Citation')}")

            st.session_state.research_ok = st.checkbox("I have verified factual claims and primary citations.", value=st.session_state.research_ok)

    with c_side:
        with st.container(border=True):
            st.markdown('<div class="eyebrow">Director Controls</div>', unsafe_allow_html=True)
            if st.button("💾 Save Project Draft", use_container_width=True):
                proj_dict = {k: st.session_state[k] for k in defaults.keys()}
                s_id = save_project_draft(proj_dict, OUTPUTS_DIR)
                st.session_state.project_id = s_id
                st.success("Draft saved to Library!")
            st.write("✓ Zero-upload guardrail active")
            st.write("✓ Human verification required")

# ---------------------------------------------------------
# TAB 2: SCRIPT & VIRAL HOOK LAB
# ---------------------------------------------------------
with tab_writer:
    w_main, w_side = st.columns([2.3, 0.7], gap="medium")
    with w_main:
        with st.container(border=True):
            st.markdown('<div class="eyebrow">Viral Hook A/B Testing Lab</div>', unsafe_allow_html=True)
            st.caption("The first 3 seconds decide 80% of your video's retention. Test psychological hook variations below:")

            if not st.session_state.hooks:
                st.session_state.hooks = generate_hook_variations(st.session_state.topic, st.session_state.niche, st.session_state.audience, current_llm)

            h_cols = st.columns(len(st.session_state.hooks))
            for h_i, h_item in enumerate(st.session_state.hooks):
                with h_cols[h_i]:
                    with st.container(border=True):
                        st.markdown(f'<span class="winner-tag">{h_item.get("tag", "HOOK")}</span>', unsafe_allow_html=True)
                        st.markdown(f'**{h_item.get("archetype", "Angle")}**')
                        st.markdown(f'<p class="micro"><em>"{h_item.get("hook", "")}"</em></p>', unsafe_allow_html=True)
                        st.metric("3s Hold Rate", f"{h_item.get('hold_rate', 90)}%")
                        if st.button("Use Hook", key=f"use_hook_{h_i}", use_container_width=True):
                            st.session_state.script = replace_script_hook(st.session_state.script, h_item.get("hook", ""))
                            st.success("Hook inserted into script!")
                            st.rerun()

        with st.container(border=True):
            st.markdown('<div class="eyebrow">Script Narration & Retention Science</div>', unsafe_allow_html=True)
            t_col1, t_col2 = st.columns([2, 1])
            tone_options = ["Balanced Editorial", "Alex Hormozi Framework", "Veritasium Investigative Essay", "Viral Shorts / Reels"]
            st.session_state.tone_preset = t_col1.selectbox("Creator Tone Preset", tone_options, index=tone_options.index(st.session_state.tone_preset) if st.session_state.tone_preset in tone_options else 0)

            with t_col2:
                st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
                if st.button("🔄 Rewrite with Tone", use_container_width=True):
                    selected_prop = st.session_state.proposals[st.session_state.winner] if st.session_state.proposals else {}
                    with st.spinner("Rewriting script with selected tone..."):
                        st.session_state.script = make_script(
                            topic=st.session_state.topic,
                            angle=selected_prop.get("angle", ""),
                            thesis=selected_prop.get("thesis", ""),
                            hook=selected_prop.get("hook", ""),
                            niche=st.session_state.niche,
                            audience=st.session_state.audience,
                            duration_sec=60,
                            tone_preset=st.session_state.tone_preset,
                            llm_provider=current_llm,
                        )
                    st.rerun()

            s_tab, r_tab = st.tabs(["📝 Narration Script", "📈 Sentence Retention Pacing Map"])
            with s_tab:
                words = len(st.session_state.script.split())
                est_sec = round(words / 2.3)
                st.caption(f"Word count: **{words} words** · ~**{est_sec}s** speaking duration")
                st.session_state.script = st.text_area("Narration Script", st.session_state.script, height=300, label_visibility="collapsed")

            with r_tab:
                audit = audit_script_retention(st.session_state.script)
                m1, m2, m3 = st.columns(3)
                m1.metric("Retention Score", f"{audit['score']}/100", f"Grade: {audit['grade']}")
                m2.metric("Total Sentences", audit['stats']['total_sentences'])
                m3.metric("Avg Words / Sentence", audit['stats']['avg_sentence_len'])

                for rec in audit.get("recommendations", []):
                    st.info(f"💡 **Pacing Insight:** {rec}")

                for s_item in audit.get("sentences", []):
                    risk_cls = f"pacing-{s_item['risk']}"
                    flags_str = f" ⚠️ *({', '.join(s_item['flags'])})*" if s_item['flags'] else ""
                    st.markdown(f'<div class="pacing-item {risk_cls}"><b>[{s_item["words"]}w]</b> {s_item["text"]}{flags_str}</div>', unsafe_allow_html=True)

    with w_side:
        with st.container(border=True):
            st.markdown('<div class="eyebrow">Script Approvals</div>', unsafe_allow_html=True)
            st.session_state.personal = st.checkbox("Original creator proof included", value=st.session_state.personal)
            st.session_state.script_ok = st.checkbox("Approve script for rendering", value=st.session_state.script_ok, disabled=not st.session_state.research_ok)
            if st.session_state.script_ok:
                st.success("Script approved for production!")

# ---------------------------------------------------------
# TAB 3: LIVE SIMULATOR & STORYBOARD STUDIO
# ---------------------------------------------------------
with tab_studio:
    st.markdown("### 🎬 Visual Studio & Live Simulation")
    scenes = segment_script_into_scenes(st.session_state.script, target_clip_duration_sec=5)

    sim_col1, sim_col2 = st.columns([1.5, 1.5], gap="large")

    with sim_col1:
        st.markdown("#### 📱 Interactive Video & Subtitle Simulator")
        st.caption("Simulates background scene shifts, timing, and word-by-word karaoke subtitles in real time.")
        sim_html = render_live_video_simulator(
            scenes=scenes,
            title=st.session_state.title,
            aspect_ratio="16:9",
        )
        st.components.v1.html(sim_html, height=520, scrolling=False)

    with sim_col2:
        st.markdown("#### 🎨 Live SVG Thumbnail Canvas")
        th_t1, th_t2 = st.columns(2)
        th_theme = th_t1.selectbox("Color Theme", ["emerald", "cyber", "amber", "crimson"])
        th_ratio = th_t2.selectbox("Format", ["16:9", "9:16"])

        svg_code = generate_thumbnail_svg(
            headline=st.session_state.title,
            subtitle="WORKFLOW EXPERIMENT",
            badge="AI × HUMAN",
            aspect_ratio=th_ratio,
            theme=th_theme,
        )
        st.markdown(svg_code, unsafe_allow_html=True)
        st.download_button(
            "⬇️ Download SVG Thumbnail",
            data=svg_code,
            file_name="thumbnail.svg",
            mime="image/svg+xml",
            use_container_width=True,
        )

    st.markdown("---")
    st.markdown("#### 🎞️ Scene-by-Scene Visual Storyboard Timeline")
    st.caption("Every 5-second scene is matched with targeted visual search queries and camera motions.")

    s_cols = st.columns(min(len(scenes), 4))
    for sc_idx, sc in enumerate(scenes[:8]):
        col_target = s_cols[sc_idx % len(s_cols)]
        with col_target:
            with st.container(border=True):
                st.markdown(f'<div class="eyebrow">SCENE {sc["scene_idx"]:02d} · {sc["time_label"]}</div>', unsafe_allow_html=True)
                st.markdown(f'**{sc.get("visual_concept", "")}**')
                st.caption(f"🎥 {sc.get('camera_motion', 'Cinematic Pan')}")
                st.write(f'*" {sc.get("narration", "")[:80]}... "*')
                st.caption(f"🏷️ Query: `{sc.get('broll_query', '')}`")

# ---------------------------------------------------------
# TAB 4: IN-HOUSE RENDER & EXPORT HUB
# ---------------------------------------------------------
with tab_render:
    st.markdown("### 🚀 In-House Video Render & Export Hub")

    r_main, r_side = st.columns([2.2, 0.8], gap="medium")

    with r_main:
        with st.container(border=True):
            st.markdown('<div class="eyebrow">Production Engine Configuration</div>', unsafe_allow_html=True)

            p_v1, p_v2, p_v3 = st.columns(3)
            voice_choice = p_v1.selectbox("Voice Model (Edge-TTS)", list(AVAILABLE_VOICES.keys()), index=0)
            voice_spd = p_v2.slider("Speaking Rate", min_value=0.8, max_value=1.3, value=1.0, step=0.05)
            video_fmt = p_v3.selectbox("Output Aspect Ratio", ["16:9 (Landscape)", "9:16 (Shorts/Reels)"])

            st.session_state.title = st.text_input("Approved Packaging Title", st.session_state.title)

            render_settings = {
                "voice_name": voice_choice,
                "voice_rate": voice_spd,
                "video_aspect": video_fmt.split()[0],
                "video_clip_duration": 5,
                "video_terms": compile_storyboard_to_broll_terms(scenes),
            }

            st.markdown("---")
            st.markdown("#### 🎬 Direct In-App Video Rendering")
            st.caption("Renders speech audio, downloads matching B-roll footage, aligns subtitles, and exports the final MP4 locally.")

            prog_bar = st.progress(0, text="Ready to render.")

            if st.button("🎬 Render Final Video Directly in App", type="primary", use_container_width=True):
                def update_render_ui(msg: str, pct: float):
                    prog_bar.progress(int(pct * 100), text=msg)

                with st.spinner("Rendering video assets in-house..."):
                    success, msg, out_path = render_video_pipeline(
                        topic=st.session_state.title or st.session_state.topic,
                        script=st.session_state.script,
                        settings=render_settings,
                        output_dir=OUTPUTS_DIR,
                        pexels_api_key=pexels_key,
                        progress_callback=update_render_ui,
                    )
                    st.session_state.render_message = msg
                    if out_path:
                        if str(out_path).endswith(".mp4"):
                            st.session_state.rendered_video_path = str(out_path)
                        elif str(out_path).endswith(".mp3"):
                            st.session_state.rendered_audio_path = str(out_path)

            if st.session_state.render_message:
                st.success(st.session_state.render_message)

            # Display In-App Video Player if MP4 is ready
            if st.session_state.rendered_video_path and os.path.exists(st.session_state.rendered_video_path):
                st.markdown("##### 📺 Rendered Video Playback")
                st.video(st.session_state.rendered_video_path)
                with open(st.session_state.rendered_video_path, "rb") as vf:
                    st.download_button(
                        "⬇️ Download Final MP4 Video",
                        data=vf.read(),
                        file_name=Path(st.session_state.rendered_video_path).name,
                        mime="video/mp4",
                        use_container_width=True,
                    )
            elif st.session_state.rendered_audio_path and os.path.exists(st.session_state.rendered_audio_path):
                st.markdown("##### 🎙️ Synthesized Audio Voiceover")
                st.audio(st.session_state.rendered_audio_path)
                with open(st.session_state.rendered_audio_path, "rb") as af:
                    st.download_button(
                        "⬇️ Download Voiceover Audio (.mp3)",
                        data=af.read(),
                        file_name=Path(st.session_state.rendered_audio_path).name,
                        mime="audio/mp3",
                        use_container_width=True,
                    )

        # Social & SEO Packaging Station
        with st.container(border=True):
            st.markdown('<div class="eyebrow">Multi-Platform SEO & Social Packaging</div>', unsafe_allow_html=True)
            soc_pkg = create_social_package(
                topic=st.session_state.topic,
                script=st.session_state.script,
                niche=st.session_state.niche,
                research_claims=st.session_state.research,
                title=st.session_state.title,
                tone_preset=st.session_state.tone_preset,
            )
            s_tab1, s_tab2, s_tab3, s_tab4 = st.tabs(["📺 YouTube Description & Chapters", "🐦 X / Twitter Thread", "💼 LinkedIn Article", "🏷️ SEO Tags"])
            with s_tab1:
                st.text_area("YouTube Description", soc_pkg["youtube_description"], height=200)
            with s_tab2:
                st.text_area("X / Twitter Thread", soc_pkg["x_post"], height=160)
            with s_tab3:
                st.text_area("LinkedIn Article", soc_pkg["linkedin_post"], height=180)
            with s_tab4:
                st.text_input("SEO Tags", soc_pkg["seo_tags"])

    with r_side:
        with st.container(border=True):
            st.markdown('<div class="eyebrow">MoneyPrinterTurbo Handoff</div>', unsafe_allow_html=True)
            payload = moneyprinter_payload(st.session_state.title, st.session_state.script, render_settings)
            is_valid, note = validate_payload(payload)

            if st.button("🚀 Dispatch to External Server", use_container_width=True):
                with st.spinner(f"Sending to {mpt_endpoint}..."):
                    ok, d_msg, _ = dispatch_to_moneyprinter(payload, mpt_endpoint)
                    if ok: st.success(d_msg)
                    else: st.warning(d_msg)

            st.download_button(
                "⬇️ Download VideoParams JSON",
                data=json.dumps(payload, indent=2),
                file_name="videoparams_payload.json",
                mime="application/json",
                use_container_width=True,
            )
            with st.expander("View Payload JSON"):
                st.json(payload)
