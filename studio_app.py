from pathlib import Path

import streamlit as st

from studio.engine import Project, council, make_script, moneyprinter_payload, now_iso, research_pack, risk_check, save_handoff, score_topics, validate_payload

st.set_page_config(page_title="Signal Studio", page_icon="◉", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700&display=swap');
:root{--ink:#17201d;--muted:#66706b;--paper:#f4f1ea;--card:#fffdf8;--line:#dedbd2;--green:#1d5c47;--lime:#c9f064;--amber:#d88d2a;--red:#c45543}
.stApp{background:var(--paper);color:var(--ink);font-family:'DM Sans',sans-serif}.block-container{max-width:1320px;padding:1.3rem 2rem 3rem}
h1,h2,h3{font-family:'Manrope',sans-serif;letter-spacing:-.03em}.brand{display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line);padding:.2rem 0 1rem;margin-bottom:1rem}.brand-name{font:700 1.08rem Manrope}.brand-name b{color:var(--green)}.mode{font-size:.72rem;padding:.35rem .6rem;border:1px solid #dacb99;border-radius:99px;background:#fff6d9;color:#695317}
.hero{display:grid;grid-template-columns:1.4fr .6fr;gap:1rem;align-items:end;margin:1rem 0 1.3rem}.hero h1{font-size:2.35rem;line-height:1.02;margin:0;max-width:780px}.hero p{color:var(--muted);margin:.6rem 0 0;max-width:650px}.project-meta{text-align:right;color:var(--muted);font-size:.78rem}
.rail{display:grid;grid-template-columns:repeat(7,1fr);border:1px solid var(--line);border-radius:12px;overflow:hidden;background:var(--card);margin-bottom:1.2rem}.stage{padding:.72rem .65rem;border-right:1px solid var(--line);font-size:.72rem;color:var(--muted)}.stage:last-child{border:0}.stage span{display:block;font-weight:700;color:var(--ink);margin-bottom:.12rem}.stage.active{background:#e8f0e8}.stage.done span{color:var(--green)}
[data-testid="stVerticalBlockBorderWrapper"]{background:var(--card);border-color:var(--line)!important;border-radius:12px!important}.eyebrow{font-size:.68rem;text-transform:uppercase;letter-spacing:.12em;color:var(--green);font-weight:700}.score{font:700 1.6rem Manrope;color:var(--green)}.micro{font-size:.76rem;color:var(--muted)}
.advisor{border-top:3px solid var(--green);padding:.85rem 0}.advisor h4{margin:.15rem 0}.winner{display:inline-block;background:var(--lime);padding:.2rem .45rem;border-radius:4px;font-size:.67rem;font-weight:700;color:#203512}
.risk-low{color:var(--green)}.risk-review{color:var(--amber)}.risk-high{color:var(--red)}
.stButton>button{border-radius:8px;font-weight:600;border:1px solid var(--ink);min-height:2.5rem}.stButton>button[kind="primary"]{background:var(--green);border-color:var(--green)}
.stTextInput input,.stTextArea textarea,.stSelectbox [data-baseweb="select"]{background:#fffefa;border-color:var(--line)}
@media(max-width:900px){
 .block-container{padding:1rem 1rem 3rem;max-width:100%}
 .hero{grid-template-columns:1fr;gap:.7rem}.project-meta{text-align:left}
 .rail{grid-template-columns:repeat(4,minmax(0,1fr))}
 [data-testid="stHorizontalBlock"]{flex-direction:column!important;gap:.75rem!important}
 [data-testid="column"]{width:100%!important;flex:1 1 100%!important;min-width:0!important}
 .hero h1{font-size:clamp(1.75rem,7vw,2.15rem);max-width:100%}
 .hero p{font-size:.92rem}.brand{align-items:flex-start;gap:.65rem}.mode{white-space:nowrap}
}
@media(max-width:560px){
 .block-container{padding:.75rem .7rem 2.5rem}
 .brand{flex-direction:column}.rail{grid-template-columns:repeat(2,minmax(0,1fr))}
 .stage{min-height:58px;padding:.62rem .55rem}.hero{margin:.75rem 0 1rem}
 .hero h1{font-size:1.72rem}.project-meta{display:none}
 [data-testid="stVerticalBlockBorderWrapper"]{border-radius:9px!important}
 .stButton>button{width:100%}
}
</style>""", unsafe_allow_html=True)

defaults = {"stage": 0, "niche": "AI productivity", "audience": "solo creators with limited time", "goal": "Build trust with a useful weekly video", "topics": [], "topic": "", "proposals": [], "winner": 0, "script": "", "research": [], "research_ok": False, "script_ok": False, "personal": True, "title": "", "handoff": ""}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

st.markdown('<div class="brand"><div class="brand-name"><b>◉</b> SIGNAL STUDIO <span class="micro">× MoneyPrinterTurbo</span></div><div class="mode">DEMO PROVIDERS · NO AUTO-PUBLISH</div></div>', unsafe_allow_html=True)
st.markdown('<div class="hero"><div><div class="eyebrow">Human-led AI production</div><h1>From a promising signal to a video worth publishing.</h1><p>A gated editorial workflow for original, researched YouTube content—then a clean handoff to MoneyPrinterTurbo for production.</p></div><div class="project-meta">PROJECT 001<br><b>AI CREATOR SYSTEMS</b></div></div>', unsafe_allow_html=True)

stages = ["Brief", "Signals", "Council", "Research", "Script", "Production", "Handoff"]
rail = '<div class="rail">' + ''.join(f'<div class="stage {"done" if i < st.session_state.stage else "active" if i == st.session_state.stage else ""}"><span>{i+1:02d} · {s}</span>{"Complete" if i < st.session_state.stage else "In focus" if i == st.session_state.stage else "Waiting"}</div>' for i,s in enumerate(stages)) + '</div>'
st.markdown(rail, unsafe_allow_html=True)

main, side = st.columns([2.25, .75], gap="medium")
with main:
    with st.container(border=True):
        st.markdown('<div class="eyebrow">01 · Creative brief</div>', unsafe_allow_html=True)
        c1,c2 = st.columns(2)
        st.session_state.niche = c1.text_input("Niche / territory", st.session_state.niche)
        st.session_state.audience = c2.text_input("Primary audience", st.session_state.audience)
        st.session_state.goal = st.text_input("Editorial goal", st.session_state.goal)
        if st.button("Find topic signals", type="primary", use_container_width=True):
            st.session_state.topics = score_topics(st.session_state.niche, st.session_state.audience); st.session_state.stage=max(st.session_state.stage,1)

    if st.session_state.topics:
        st.markdown("#### Topic signals")
        cols=st.columns(3)
        for i,item in enumerate(st.session_state.topics):
            with cols[i]:
                with st.container(border=True):
                    st.markdown(f'<div class="score">{item["score"]}</div><b>{item["topic"]}</b><p class="micro">{item["signal"]}</p>', unsafe_allow_html=True)
                    if st.button("Develop this", key=f"topic_{i}", use_container_width=True):
                        st.session_state.topic=item["topic"]; st.session_state.proposals,st.session_state.winner,_=council(item["topic"]); st.session_state.script=make_script(item["topic"],st.session_state.proposals[st.session_state.winner]["angle"]); st.session_state.research=research_pack(item["topic"]); st.session_state.title=item["topic"]; st.session_state.stage=max(st.session_state.stage,2); st.rerun()

    if st.session_state.proposals:
        st.markdown("#### Council board")
        cols=st.columns(3)
        for i,p in enumerate(st.session_state.proposals):
            with cols[i]:
                with st.container(border=True):
                    st.markdown(f'<div class="advisor">{("<span class=winner>JUDGE PICK</span>" if i==st.session_state.winner else "")}<p class="micro">{p["advisor"]}</p><h4>{p["angle"]}</h4><p>{p["hook"]}</p><p class="micro">{p["thesis"]}</p></div>', unsafe_allow_html=True)
                    if st.button("Use this angle",key=f"angle_{i}"): st.session_state.winner=i; st.session_state.script=make_script(st.session_state.topic,p["angle"]); st.rerun()

        with st.container(border=True):
            st.markdown('<div class="eyebrow">04 · Research checkpoint</div>',unsafe_allow_html=True)
            st.caption("Prototype evidence is intentionally marked. Replace demo signals with live, cited research before publishing.")
            for row in st.session_state.research:
                a,b,c=st.columns([2.1,1,1.4]); a.write(row["claim"]); b.caption(row["status"]); c.caption(row["source"])
            st.session_state.research_ok=st.checkbox("I reviewed these claims and will replace demo evidence with verified sources",value=st.session_state.research_ok)
            if st.session_state.research_ok: st.session_state.stage=max(st.session_state.stage,4)

        with st.container(border=True):
            st.markdown('<div class="eyebrow">05 · Script editor</div>',unsafe_allow_html=True)
            st.session_state.script=st.text_area("Approved narration",st.session_state.script,height=330,label_visibility="collapsed")
            x,y=st.columns(2); st.session_state.personal=x.checkbox("Includes my test, experience, or original analysis",value=st.session_state.personal); st.session_state.script_ok=y.checkbox("Approve script for production",value=st.session_state.script_ok,disabled=not st.session_state.research_ok)
            if st.session_state.script_ok: st.session_state.stage=max(st.session_state.stage,5)

        with st.container(border=True):
            st.markdown('<div class="eyebrow">06 · Production & packaging</div>',unsafe_allow_html=True)
            a,b,c=st.columns(3)
            voice=a.selectbox("Voice",["en-US-JennyNeural-Female","en-US-GuyNeural-Male","Chatterbox · reference voice"])
            broll=b.selectbox("B-roll matching",["Semantic","Sequential","Random"])
            aspect=c.selectbox("Format",["16:9","9:16","1:1"])
            d,e,f=st.columns(3)
            subtitles=d.selectbox("Subtitles",["Word highlight","Standard","Off"])
            music=e.selectbox("Music",["Light ambient","None","Local track"])
            clip=f.slider("B-roll clip length",3,10,5)
            st.session_state.title=st.text_input("Primary title",st.session_state.title)
            t1,t2,t3=st.columns(3); t1.caption("ALT 01");t1.write("The AI Workflow I Actually Kept");t2.caption("ALT 02");t2.write("Stop Automating the Wrong Part");t3.caption("THUMBNAIL");t3.write("AUTOMATE LESS. SHIP BETTER.")
            settings={"voice_name":voice,"video_concat_mode":broll.lower(),"video_aspect":aspect,"video_clip_duration":clip,"subtitle_enabled":subtitles!="Off","enable_word_highlighting":subtitles=="Word highlight","bgm_type":"none" if music=="None" else "random"}
            report=risk_check(st.session_state.script,st.session_state.title,st.session_state.personal,st.session_state.research_ok)
            st.markdown(f'**Monetization review:** <span class="risk-{report["level"].lower()}">{report["score"]}/100 · {report["level"]}</span>',unsafe_allow_html=True)
            for finding in report["findings"]: st.caption("• "+finding)
            ready=st.session_state.research_ok and st.session_state.script_ok and report["score"]<60
            if st.button("Create MoneyPrinterTurbo handoff",type="primary",use_container_width=True,disabled=not ready):
                payload=moneyprinter_payload(st.session_state.topic,st.session_state.script,settings); valid,note=validate_payload(payload)
                if valid:
                    project=Project(st.session_state.niche,st.session_state.audience,st.session_state.goal,st.session_state.topic,st.session_state.script,st.session_state.research_ok,st.session_state.script_ok,settings,report["score"],now_iso())
                    st.session_state.handoff=str(save_handoff(Path(__file__).parent/"studio_outputs",project,payload)); st.session_state.stage=6; st.success(f"Handoff ready · {note}")
                else: st.error("Payload validation failed: "+note)

with side:
    with st.container(border=True):
        st.markdown('<div class="eyebrow">Readiness</div>',unsafe_allow_html=True)
        checks=[("Topic selected",bool(st.session_state.topic)),("Council judged",bool(st.session_state.proposals)),("Research approved",st.session_state.research_ok),("Script approved",st.session_state.script_ok),("Handoff ready",bool(st.session_state.handoff))]
        for label,ok in checks: st.write(("✓ " if ok else "○ ")+label)
    with st.container(border=True):
        st.markdown('<div class="eyebrow">Guardrails</div>',unsafe_allow_html=True)
        st.write("Human approval required")
        st.write("No automatic upload")
        st.write("Demo evidence labeled")
        st.write("Upstream payload validated")
    if st.session_state.handoff:
        with st.container(border=True):
            st.markdown('<div class="eyebrow">Ready for renderer</div>',unsafe_allow_html=True)
            st.success("Editorial gates passed")
            st.code(st.session_state.handoff,language=None)

