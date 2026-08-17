from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st

from studio.ai_providers import get_llm_provider
from studio.engine import (
    Project,
    audit_script_retention,
    create_social_package,
    delete_project_draft,
    dispatch_to_moneyprinter,
    fetch_research_pack,
    generate_packaging,
    generate_thumbnail_svg,
    list_saved_projects,
    load_project_draft,
    make_script,
    moneyprinter_payload,
    now_iso,
    risk_check,
    run_council,
    save_handoff,
    save_project_draft,
    score_topics,
    validate_payload,
)

st.set_page_config(
    page_title="Signal Studio × MoneyPrinterTurbo",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

OUTPUTS_DIR = Path(__file__).parent / "studio_outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Manrope:wght@600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
  --ink: #121916;
  --muted: #5a6660;
  --paper: #f7f5ef;
  --card: #ffffff;
  --line: #dedbd2;
  --green: #17543f;
  --green-light: #e6f3ed;
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
  max-width: 1380px;
  padding: 1.2rem 2rem 3.5rem;
}

h1, h2, h3, h4 {
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
  font: 800 1.25rem 'Manrope', sans-serif;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.brand-name b {
  color: var(--green);
}

.mode-badge {
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.35rem 0.75rem;
  border-radius: 99px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.mode-demo {
  background: #fef9c3;
  color: #854d0e;
  border: 1px solid #fde047;
}

.mode-live {
  background: #dcfce7;
  color: #166534;
  border: 1px solid #86efac;
}

.hero {
  display: grid;
  grid-template-columns: 1.6fr 0.4fr;
  gap: 1.5rem;
  align-items: end;
  margin: 0.5rem 0 1.4rem;
}

.hero h1 {
  font-size: 2.35rem;
  line-height: 1.05;
  margin: 0.2rem 0 0.5rem;
}

.hero p {
  color: var(--muted);
  margin: 0;
  font-size: 1rem;
  line-height: 1.45;
}

.project-meta {
  text-align: right;
  color: var(--muted);
  font-size: 0.8rem;
  line-height: 1.4;
  border-left: 2px solid var(--line);
  padding-left: 1rem;
}

.rail {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
  background: var(--card);
  margin-bottom: 1.4rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}

.stage {
  padding: 0.75rem 0.65rem;
  border-right: 1px solid var(--line);
  font-size: 0.73rem;
  color: var(--muted);
  transition: all 0.2s ease;
}

.stage:last-child {
  border-right: 0;
}

.stage span {
  display: block;
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 0.15rem;
}

.stage.active {
  background: var(--green-light);
  border-bottom: 2px solid var(--green);
}

.stage.done span {
  color: var(--green);
}

[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--card);
  border-color: var(--line) !important;
  border-radius: 12px !important;
  box-shadow: 0 1px 4px rgba(0,0,0,0.02);
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
  font: 800 1.8rem 'Manrope', sans-serif;
  color: var(--green);
  line-height: 1;
}

.micro {
  font-size: 0.78rem;
  color: var(--muted);
  line-height: 1.35;
}

.advisor-card {
  border-top: 3px solid var(--green);
  padding: 0.9rem 0;
}

.advisor-card.winner {
  border-top-color: #84cc16;
}

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

.risk-pill {
  display: inline-block;
  padding: 0.2rem 0.6rem;
  border-radius: 99px;
  font-weight: 700;
  font-size: 0.8rem;
}

.risk-low {
  background: var(--green-light);
  color: var(--green);
  border: 1px solid #a7f3d0;
}

.risk-review {
  background: var(--amber-light);
  color: var(--amber);
  border: 1px solid #fde68a;
}

.risk-high {
  background: var(--red-light);
  color: var(--red);
  border: 1px solid #fecaca;
}

.source-link {
  font-size: 0.78rem;
  color: var(--green);
  text-decoration: none;
  font-weight: 600;
}

.source-link:hover {
  text-decoration: underline;
}

.retention-box {
  padding: 0.8rem;
  border-radius: 8px;
  background: #f8faf9;
  border: 1px solid var(--line);
  margin-bottom: 0.8rem;
}

.pacing-item {
  padding: 0.45rem 0.6rem;
  border-radius: 6px;
  margin-bottom: 0.35rem;
  font-size: 0.85rem;
  line-height: 1.4;
}

.pacing-green { background: #f0fdf4; border-left: 3px solid #22c55e; }
.pacing-yellow { background: #fefce8; border-left: 3px solid #eab308; }
.pacing-red { background: #fef2f2; border-left: 3px solid #ef4444; }

.stButton > button {
  border-radius: 8px;
  font-weight: 600;
  border: 1px solid var(--ink);
  min-height: 2.5rem;
  transition: all 0.15s ease;
}

.stButton > button[kind="primary"] {
  background: var(--green);
  border-color: var(--green);
  color: #ffffff;
}

.stButton > button[kind="primary"]:hover {
  background: #113d2e;
  border-color: #113d2e;
}
</style>""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar: Provider, Model, and Project Library
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### 🗂️ Project Library")
    saved_projects = list_saved_projects(OUTPUTS_DIR)
    if saved_projects:
        proj_options = {p.get("project_id", ""): f"{p.get('topic', 'Untitled')[:28]} ({p.get('updated_at', '')[:10]})" for p in saved_projects}
        selected_proj_id = st.selectbox("Saved Projects", options=list(proj_options.keys()), format_func=lambda k: proj_options.get(k, k))
        lp1, lp2 = st.columns(2)
        if lp1.button("📂 Load Project", use_container_width=True):
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
    st.markdown("### ⚙️ Engine Settings")

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
            gemini_key = st.text_input(
                "Gemini API Key",
                value=os.getenv("GEMINI_API_KEY", ""),
                type="password",
                help="Get a key at aistudio.google.com",
            )
            model_name = st.selectbox("Model", ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"], index=0)
        elif llm_choice == "OpenAI / Local Ollama":
            openai_key = st.text_input("API Key (Optional for Ollama)", value=os.getenv("OPENAI_API_KEY", ""), type="password")
            custom_base_url = st.text_input("Base URL", value="https://api.openai.com/v1")
            model_name = st.text_input("Model Name", value="gpt-4o-mini")

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

    with st.expander("🚀 MoneyPrinterTurbo Renderer", expanded=False):
        mpt_endpoint = st.text_input(
            "API Endpoint",
            value="http://127.0.0.1:8080/api/v1/generate",
            help="Local or remote MoneyPrinterTurbo Extended API URL",
        )

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
    "stage": 0,
    "project_id": "",
    "niche": "AI productivity workflows",
    "audience": "solo creators and freelancers with limited time",
    "goal": "Build trust with a practical, step-by-step weekly video",
    "topics": [],
    "topic": "",
    "proposals": [],
    "winner": 0,
    "judge_reasoning": "",
    "tone_preset": "Balanced Editorial",
    "script": "",
    "research": [],
    "research_ok": False,
    "script_ok": False,
    "personal": True,
    "title": "",
    "packaging": {},
    "thumbnail_theme": "emerald",
    "broll_tags": "creator desk, workflow diagram, editing timeline, screen capture, analytics",
    "handoff_path": "",
    "social_package": {},
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# ---------------------------------------------------------
# Header & Navigation Rail
# ---------------------------------------------------------
mode_label = f"LIVE AI · {current_llm.provider_name.upper()}" if is_live_mode else "DEMO MODE · ZERO API KEYS"
mode_class = "mode-live" if is_live_mode else "mode-demo"

st.markdown(
    f'<div class="brand"><div class="brand-name"><b>◉</b> SIGNAL STUDIO <span class="micro">× MoneyPrinterTurbo</span></div>'
    f'<div class="mode-badge {mode_class}">{mode_label}</div></div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero"><div><div class="eyebrow">Creator Workstation · Human-Led AI Video</div>'
    '<h1>From an editorial signal to a video worth publishing.</h1>'
    '<p>Multi-advisor council ideation, retention-calibrated scripting, live research citations, and automated packaging handoff.</p>'
    '</div><div class="project-meta">WORKSTATION ACTIVE<br><b>MONEYPRINTER PIPELINE</b></div></div>',
    unsafe_allow_html=True,
)

stages = ["Brief", "Signals", "Council", "Research", "Script", "Production", "Handoff"]
rail_html = '<div class="rail">' + "".join(
    f'<div class="stage {"done" if i < st.session_state.stage else "active" if i == st.session_state.stage else ""}">'
    f"<span>{i+1:02d} · {s}</span>"
    f'{"✓ Done" if i < st.session_state.stage else "In focus" if i == st.session_state.stage else "Waiting"}</div>'
    for i, s in enumerate(stages)
) + "</div>"
st.markdown(rail_html, unsafe_allow_html=True)

# ---------------------------------------------------------
# Main Workflow Layout
# ---------------------------------------------------------
main_col, side_col = st.columns([2.3, 0.7], gap="medium")

with main_col:
    # --- STAGE 01: CREATIVE BRIEF ---
    with st.container(border=True):
        st.markdown('<div class="eyebrow">01 · Creative Brief</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        st.session_state.niche = c1.text_input("Niche / Territory", st.session_state.niche)
        st.session_state.audience = c2.text_input("Primary Target Audience", st.session_state.audience)
        st.session_state.goal = st.text_input("Editorial Goal", st.session_state.goal)

        b_col1, b_col2 = st.columns([1.5, 1])
        with b_col1:
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
                    st.session_state.stage = max(st.session_state.stage, 1)
                    st.rerun()
        with b_col2:
            if st.button("💾 Save Project Draft", use_container_width=True):
                proj_dict = {k: st.session_state[k] for k in defaults.keys()}
                saved_id = save_project_draft(proj_dict, OUTPUTS_DIR)
                st.session_state.project_id = saved_id
                st.success("Draft saved to Library!")

    # --- STAGE 02: TOPIC SIGNALS ---
    if st.session_state.topics:
        st.markdown("#### 02 · Evaluated Topic Signals")
        cols = st.columns(len(st.session_state.topics))
        for i, item in enumerate(st.session_state.topics):
            with cols[i]:
                with st.container(border=True):
                    st.markdown(
                        f'<div class="score-badge">{item.get("score", 90)}</div>'
                        f'<b>{item["topic"]}</b><p class="micro">{item.get("signal", "")}</p>',
                        unsafe_allow_html=True,
                    )
                    if st.button("Develop This Angle", key=f"topic_select_{i}", use_container_width=True):
                        st.session_state.topic = item["topic"]
                        with st.spinner("Convening 3-Advisor Council & conducting fact check..."):
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
                            packaging_data = generate_packaging(
                                topic=item["topic"],
                                script=st.session_state.script,
                                llm_provider=current_llm,
                            )
                            st.session_state.packaging = packaging_data
                            titles = packaging_data.get("titles", [item["topic"]])
                            st.session_state.title = titles[0] if titles else item["topic"]
                            st.session_state.broll_tags = ", ".join(packaging_data.get("broll_tags", ["creator desk", "workflow"]))
                            st.session_state.stage = max(st.session_state.stage, 2)
                            st.rerun()

    # --- STAGE 03: COUNCIL BOARD ---
    if st.session_state.proposals:
        st.markdown("#### 03 · 3-Advisor Council Board")
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
                        with st.spinner("Regenerating script with selected angle..."):
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

        # --- STAGE 04: RESEARCH CHECKPOINT ---
        with st.container(border=True):
            st.markdown('<div class="eyebrow">04 · Research & Fact-Check Checkpoint</div>', unsafe_allow_html=True)
            st.caption("Human-gated evidence verification: review factual claims and primary citations before committing to production.")

            for r_idx, row in enumerate(st.session_state.research):
                a, b, c = st.columns([2.2, 1.0, 1.2])
                a.write(f"**•** {row.get('claim', '')}")
                b.caption(f"🏷️ {row.get('status', 'Unverified')}")
                url = row.get("url", "")
                if url:
                    c.markdown(f'<a href="{url}" target="_blank" class="source-link">🔗 {row.get("source", "Primary Source")}</a>', unsafe_allow_html=True)
                else:
                    c.caption(f"📚 {row.get('source', 'Internal Citation')}")

            st.session_state.research_ok = st.checkbox(
                "I have verified these factual claims and reviewed primary source evidence.",
                value=st.session_state.research_ok,
            )
            if st.session_state.research_ok:
                st.session_state.stage = max(st.session_state.stage, 4)

        # --- STAGE 05: SCRIPT EDITOR & RETENTION AUDITOR ---
        with st.container(border=True):
            st.markdown('<div class="eyebrow">05 · Script Narration & Retention Science</div>', unsafe_allow_html=True)

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

            script_tab, retention_tab = st.tabs(["📝 Script Narration", "📈 Retention Drop-Off Analysis"])

            with script_tab:
                words = len(st.session_state.script.split())
                est_sec = round(words / 2.3)
                st.caption(f"Spoken metrics: **{words} words** · ~**{est_sec}s** speaking duration")

                st.session_state.script = st.text_area(
                    "Approved Narration",
                    st.session_state.script,
                    height=280,
                    label_visibility="collapsed",
                )

            with retention_tab:
                audit = audit_script_retention(st.session_state.script)
                r_col1, r_col2, r_col3 = st.columns(3)
                r_col1.metric("Retention Score", f"{audit['score']}/100", f"Grade: {audit['grade']}")
                r_col2.metric("Total Sentences", audit['stats']['total_sentences'])
                r_col3.metric("Avg Words / Sentence", audit['stats']['avg_sentence_len'])

                if audit.get("recommendations"):
                    for rec in audit["recommendations"]:
                        st.info(f"💡 **Pacing Insight:** {rec}")

                st.markdown("##### Sentence Pacing Map")
                for s_item in audit.get("sentences", []):
                    risk_cls = f"pacing-{s_item['risk']}"
                    flags_str = f" ⚠️ *({', '.join(s_item['flags'])})*" if s_item['flags'] else ""
                    st.markdown(f'<div class="pacing-item {risk_cls}"><b>[{s_item["words"]}w]</b> {s_item["text"]}{flags_str}</div>', unsafe_allow_html=True)

            x, y = st.columns(2)
            st.session_state.personal = x.checkbox(
                "Includes first-hand test, original experiment, or personal proof",
                value=st.session_state.personal,
            )
            st.session_state.script_ok = y.checkbox(
                "Approve script for production handoff",
                value=st.session_state.script_ok,
                disabled=not st.session_state.research_ok,
            )
            if st.session_state.script_ok:
                st.session_state.stage = max(st.session_state.stage, 5)

        # --- STAGE 06: PRODUCTION & PACKAGING & SVG THUMBNAIL ---
        with st.container(border=True):
            st.markdown('<div class="eyebrow">06 · Production, Visual Packaging & Risk Audit</div>', unsafe_allow_html=True)

            p1, p2, p3 = st.columns(3)
            voice = p1.selectbox("Voice Model", ["en-US-JennyNeural-Female", "en-US-GuyNeural-Male", "en-US-AriaNeural-Female", "en-GB-SoniaNeural-Female"])
            broll = p2.selectbox("B-Roll Sequencing", ["Semantic Matching", "Sequential", "Random"])
            aspect = p3.selectbox("Video Format", ["16:9 (Landscape)", "9:16 (Shorts/Reels)", "1:1 (Square)"])

            p4, p5, p6 = st.columns(3)
            subtitles = p4.selectbox("Subtitles", ["Word Highlight", "Standard", "Off"])
            music = p5.selectbox("Background Music", ["Light Ambient", "Upbeat Lo-Fi", "None"])
            clip_dur = p6.slider("B-roll Clip Duration (s)", min_value=3, max_value=10, value=5)

            st.session_state.broll_tags = st.text_input(
                "B-Roll Search Terms (comma-separated)",
                value=st.session_state.broll_tags,
                help="Keywords used by MoneyPrinterTurbo to query Pexels/Pixabay stock videos.",
            )

            # Title Alternatives
            st.markdown("##### Packaging Titles")
            title_opts = st.session_state.packaging.get("titles", [st.session_state.title])
            if title_opts:
                t_cols = st.columns(len(title_opts))
                for t_i, t_text in enumerate(title_opts):
                    with t_cols[t_i]:
                        st.caption(f"OPTION {t_i+1:02d}")
                        st.write(t_text)
                        if st.button("Use Title", key=f"pick_title_{t_i}"):
                            st.session_state.title = t_text
                            st.rerun()

            st.session_state.title = st.text_input("Final Approved Title", st.session_state.title)

            # Live SVG Thumbnail Canvas Preview
            st.markdown("##### 🎨 Live SVG Thumbnail Canvas")
            th_c1, th_c2 = st.columns([1.8, 1.2])

            thumb_text = st.session_state.packaging.get("thumbnail_text", "AUTOMATE LESS. SHIP BETTER.")
            thumb_vis = st.session_state.packaging.get("thumbnail_visual", "High-contrast visual comparison with minimal text.")

            with th_c2:
                theme_pick = st.selectbox("Thumbnail Palette Theme", ["emerald", "cyber", "amber", "crimson"], index=0)
                st.session_state.thumbnail_theme = theme_pick
                st.info(f"🎨 **Thumbnail Art Concept:** {thumb_vis}")
                img_prompt = st.session_state.packaging.get("image_prompt", "")
                if img_prompt:
                    st.text_area("AI Image Prompt (Midjourney / Imagen 3)", img_prompt, height=100)

            with th_c1:
                svg_markup = generate_thumbnail_svg(
                    headline=thumb_text,
                    subtitle="WORKFLOW EXPERIMENT",
                    badge="AI × HUMAN",
                    aspect_ratio="9:16" if "9:16" in aspect else "16:9",
                    theme=theme_pick,
                )
                st.markdown(svg_markup, unsafe_allow_html=True)
                st.download_button(
                    "⬇️ Download SVG Thumbnail",
                    data=svg_markup,
                    file_name=f"thumbnail_{st.session_state.topic[:20].replace(' ', '_')}.svg",
                    mime="image/svg+xml",
                    use_container_width=True,
                )

            # Risk & Monetization Audit
            settings = {
                "voice_name": voice,
                "video_concat_mode": broll.split()[0].lower(),
                "video_aspect": aspect.split()[0],
                "video_clip_duration": clip_dur,
                "subtitle_enabled": subtitles != "Off",
                "enable_word_highlighting": subtitles == "Word Highlight",
                "bgm_type": "none" if music == "None" else "random",
                "video_terms": st.session_state.broll_tags,
            }

            report = risk_check(
                script=st.session_state.script,
                title=st.session_state.title,
                personal_evidence=st.session_state.personal,
                sources_approved=st.session_state.research_ok,
            )

            risk_class = "risk-low" if report["score"] < 30 else "risk-review" if report["score"] < 60 else "risk-high"
            st.markdown(
                f'<div style="margin-top:1.2rem"><b>Monetization & Reused-Content Risk:</b> '
                f'<span class="risk-pill {risk_class}">{report["score"]}/100 · {report["level"]}</span></div>',
                unsafe_allow_html=True,
            )
            for finding in report["findings"]:
                st.caption(f"• {finding}")
            if report.get("tips"):
                for tip in report["tips"]:
                    st.caption(f"💡 *Remediation tip:* {tip}")

            ready = st.session_state.research_ok and st.session_state.script_ok and report["score"] < 60

            # --- STAGE 07: HANDOFF & MULTI-PLATFORM SOCIAL ---
            st.markdown("---")
            st.markdown('<div class="eyebrow">07 · Handoff, Dispatch & Multi-Platform Social Packaging</div>', unsafe_allow_html=True)

            payload = moneyprinter_payload(
                topic=st.session_state.title or st.session_state.topic,
                script=st.session_state.script,
                settings=settings,
            )
            is_valid, validation_note = validate_payload(payload)

            h_col1, h_col2 = st.columns(2)
            with h_col1:
                if st.button("📁 Save Handoff Artifact", type="primary", use_container_width=True, disabled=not ready):
                    if is_valid:
                        soc_pkg = create_social_package(
                            topic=st.session_state.topic,
                            script=st.session_state.script,
                            niche=st.session_state.niche,
                            research_claims=st.session_state.research,
                            title=st.session_state.title,
                            tone_preset=st.session_state.tone_preset,
                        )
                        st.session_state.social_package = soc_pkg

                        proj = Project(
                            niche=st.session_state.niche,
                            audience=st.session_state.audience,
                            goal=st.session_state.goal,
                            topic=st.session_state.topic,
                            script=st.session_state.script,
                            research_approved=st.session_state.research_ok,
                            script_approved=st.session_state.script_ok,
                            settings=settings,
                            risk_score=report["score"],
                            created_at=now_iso(),
                            provider_info={"llm": current_llm.provider_name},
                            packaging=st.session_state.packaging,
                            social_package=soc_pkg,
                        )
                        out_path = save_handoff(OUTPUTS_DIR, proj, payload)
                        st.session_state.handoff_path = str(out_path)
                        st.session_state.stage = 6
                        st.success(f"Handoff saved to `{out_path.name}` ({validation_note})")
                    else:
                        st.error(f"Payload validation failed: {validation_note}")

            with h_col2:
                if st.button("🚀 Dispatch to MoneyPrinterTurbo API", use_container_width=True, disabled=not ready):
                    with st.spinner(f"Connecting to {mpt_endpoint}..."):
                        ok, msg, data = dispatch_to_moneyprinter(payload, endpoint_url=mpt_endpoint)
                        if ok:
                            st.success(f"Dispatched: {msg}")
                        else:
                            st.warning(f"{msg}")

            # Social Repurposing Station
            if st.session_state.script:
                soc_pkg = create_social_package(
                    topic=st.session_state.topic,
                    script=st.session_state.script,
                    niche=st.session_state.niche,
                    research_claims=st.session_state.research,
                    title=st.session_state.title,
                    tone_preset=st.session_state.tone_preset,
                )
                st.session_state.social_package = soc_pkg

                st.markdown("##### 📦 Multi-Platform Repurposing & SEO Station")
                s_tab1, s_tab2, s_tab3, s_tab4 = st.tabs(["📺 YouTube Description & Chapters", "🐦 X / Twitter Thread", "💼 LinkedIn Article", "🏷️ SEO Tags"])

                with s_tab1:
                    st.text_area("YouTube Description (with Timestamps & Citations)", soc_pkg["youtube_description"], height=220)
                with s_tab2:
                    st.text_area("X / Twitter Post", soc_pkg["x_post"], height=160)
                with s_tab3:
                    st.text_area("LinkedIn Authority Post", soc_pkg["linkedin_post"], height=180)
                with s_tab4:
                    st.text_input("SEO Tags", soc_pkg["seo_tags"])

            if st.session_state.handoff_path or ready:
                st.download_button(
                    label="⬇️ Download VideoParams JSON",
                    data=json.dumps(payload, indent=2),
                    file_name=f"moneyprinter_{st.session_state.topic[:30].replace(' ', '_')}.json",
                    mime="application/json",
                    use_container_width=True,
                )
                with st.expander("📄 View Generation Payload (VideoParams JSON)", expanded=False):
                    st.json(payload)

with side_col:
    with st.container(border=True):
        st.markdown('<div class="eyebrow">Pipeline Readiness</div>', unsafe_allow_html=True)
        checks = [
            ("Topic Selected", bool(st.session_state.topic)),
            ("Council Evaluated", bool(st.session_state.proposals)),
            ("Research Verified", st.session_state.research_ok),
            ("Script Approved", st.session_state.script_ok),
            ("Handoff Generated", bool(st.session_state.handoff_path)),
        ]
        for label, ok in checks:
            st.markdown(f"{'✅' if ok else '⚪'} **{label}**")

    with st.container(border=True):
        st.markdown('<div class="eyebrow">Editorial Guardrails</div>', unsafe_allow_html=True)
        st.write("✓ Human verification gate")
        st.write("✓ No unreviewed auto-upload")
        st.write("✓ Labeled citations & claims")
        st.write("✓ Upstream contract validated")

    if st.session_state.handoff_path:
        with st.container(border=True):
            st.markdown('<div class="eyebrow">Ready for Rendering</div>', unsafe_allow_html=True)
            st.success("Editorial Gates Passed")
            st.caption(f"Path: `{st.session_state.handoff_path}`")
