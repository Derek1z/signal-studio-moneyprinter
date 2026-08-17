from __future__ import annotations

import html
import json
from typing import Any


def render_live_video_simulator(
    scenes: list[dict[str, Any]],
    title: str = "Video Preview",
    aspect_ratio: str = "16:9",
    audio_url: str = "",
) -> str:
    """Generate an interactive HTML5/JavaScript player with synchronized animated karaoke subtitles."""
    is_vertical = "9:16" in aspect_ratio
    width_css = "340px" if is_vertical else "100%"
    aspect_css = "9 / 16" if is_vertical else "16 / 9"
    max_height_css = "600px" if is_vertical else "440px"

    clean_title = html.escape(title or "Signal Studio Video Preview")

    subtitle_events = []
    total_duration = 0.0

    for sc in scenes:
        start_t = sc.get("time_start", 0.0)
        end_t = sc.get("time_end", start_t + 5.0)
        total_duration = max(total_duration, end_t)
        words = sc.get("narration", "").split()
        if not words:
            continue
        word_dur = (end_t - start_t) / max(1, len(words))

        for w_idx, w in enumerate(words):
            w_start = start_t + (w_idx * word_dur)
            w_end = w_start + word_dur
            subtitle_events.append({
                "word": w,
                "start": round(w_start, 2),
                "end": round(w_end, 2),
                "scene_idx": sc.get("scene_idx", 1),
                "visual": sc.get("visual_concept", ""),
                "broll": sc.get("broll_query", "creator workspace"),
            })

    total_duration = max(5.0, round(total_duration, 1))
    events_json = json.dumps(subtitle_events)
    scenes_json = json.dumps(scenes)

    html_code = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800;900&family=Outfit:wght@700;800;900&display=swap');

* {{ box-sizing: border-box; margin: 0; padding: 0; user-select: none; }}
body {{ background: transparent; font-family: 'Plus Jakarta Sans', sans-serif; display: flex; justify-content: center; align-items: center; padding: 4px; }}

.player-wrapper {{
  width: {width_css};
  max-width: 820px;
  background: #090d16;
  border-radius: 18px;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.08);
  position: relative;
}}

.viewport {{
  width: 100%;
  aspect-ratio: {aspect_css};
  max-height: {max_height_css};
  position: relative;
  overflow: hidden;
  background: #0b101b;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}}

/* Dynamic Ambient Video Canvas */
.bg-canvas {{
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background: radial-gradient(circle at 60% 40%, #064e3b 0%, #022c22 45%, #050b14 100%);
  transition: all 0.7s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1;
}}

.glow-orb {{
  position: absolute;
  width: 320px; height: 320px;
  border-radius: 50%;
  background: #10b981;
  filter: blur(100px);
  opacity: 0.20;
  top: 15%; right: 5%;
  animation: pulse 4s infinite alternate ease-in-out;
  z-index: 2;
}}

@keyframes pulse {{
  0% {{ transform: scale(0.9) translate(0, 0); opacity: 0.15; }}
  100% {{ transform: scale(1.2) translate(-25px, 25px); opacity: 0.30; }}
}}

/* Equalizer Visualizer Overlay */
.equalizer-bar-container {{
  position: absolute;
  bottom: 60px;
  left: 20px;
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 24px;
  z-index: 5;
  opacity: 0.4;
}}

.eq-bar {{
  width: 3px;
  background: #10b981;
  border-radius: 2px;
  animation: eqPulse 1.2s infinite ease-in-out alternate;
}}
.eq-bar:nth-child(1) {{ height: 40%; animation-delay: 0.1s; }}
.eq-bar:nth-child(2) {{ height: 75%; animation-delay: 0.3s; }}
.eq-bar:nth-child(3) {{ height: 100%; animation-delay: 0.2s; }}
.eq-bar:nth-child(4) {{ height: 60%; animation-delay: 0.4s; }}
.eq-bar:nth-child(5) {{ height: 85%; animation-delay: 0.15s; }}

@keyframes eqPulse {{
  0% {{ height: 20%; }}
  100% {{ height: 95%; }}
}}

/* Top Overlay Badges */
.top-bar {{
  position: relative;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
}}

.brand-pill {{
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(16, 185, 129, 0.4);
  padding: 4px 10px;
  border-radius: 99px;
  font-size: 10px;
  font-weight: 800;
  color: #10b981;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  display: flex;
  align-items: center;
  gap: 5px;
}}

.brand-pill::before {{
  content: "";
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
}}

.scene-pill {{
  background: rgba(15, 23, 42, 0.75);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 4px 12px;
  border-radius: 99px;
  font-size: 11px;
  font-weight: 700;
  color: #f8fafc;
}}

/* Center Subtitle Karaoke Stage */
.subtitle-stage {{
  position: relative;
  z-index: 10;
  padding: 16px 20px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 140px;
}}

.karaoke-text {{
  font-family: 'Outfit', 'Plus Jakarta Sans', sans-serif;
  font-weight: 900;
  font-size: {"26px" if is_vertical else "34px"};
  line-height: 1.18;
  color: #f8fafc;
  text-transform: uppercase;
  text-shadow: 0 4px 20px rgba(0,0,0,0.9), 0 0 4px #000;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}}

.k-word {{
  display: inline-block;
  padding: 2px 6px;
  border-radius: 6px;
  transition: all 0.14s cubic-bezier(0.34, 1.56, 0.64, 1);
}}

.k-word.active {{
  color: #04100c;
  background: #10b981;
  transform: scale(1.16) translateY(-2px);
  box-shadow: 0 0 25px rgba(16, 185, 129, 0.7);
  text-shadow: none;
}}

.broll-hint {{
  margin-top: 14px;
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(8px);
  padding: 4px 12px;
  border-radius: 99px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}}

/* Bottom Controller Bar */
.bottom-bar {{
  position: relative;
  z-index: 10;
  background: rgba(11, 16, 27, 0.88);
  backdrop-filter: blur(16px);
  padding: 12px 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}}

.progress-track {{
  width: 100%;
  height: 5px;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 3px;
  cursor: pointer;
  position: relative;
  margin-bottom: 10px;
  overflow: hidden;
}}

.progress-fill {{
  height: 100%;
  width: 0%;
  background: linear-gradient(90deg, #10b981, #34d399);
  border-radius: 3px;
  transition: width 0.04s linear;
}}

.controls-row {{
  display: flex;
  align-items: center;
  justify-content: space-between;
}}

.btn-play {{
  background: #10b981;
  border: none;
  color: #04100c;
  font-weight: 800;
  font-size: 12px;
  letter-spacing: 0.04em;
  padding: 6px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 0 15px rgba(16, 185, 129, 0.3);
}}

.btn-play:hover {{
  background: #34d399;
  transform: scale(1.04);
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.5);
}}

.time-display {{
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  font-family: monospace;
}}
</style>
</head>
<body>

<div class="player-wrapper">
  <div class="viewport" id="viewport">
    <div class="bg-canvas" id="bgCanvas"></div>
    <div class="glow-orb"></div>

    <div class="equalizer-bar-container">
      <div class="eq-bar"></div>
      <div class="eq-bar"></div>
      <div class="eq-bar"></div>
      <div class="eq-bar"></div>
      <div class="eq-bar"></div>
    </div>

    <div class="top-bar">
      <div class="brand-pill">SIMULATOR ENGINE</div>
      <div class="scene-pill" id="sceneBadge">SCENE 01 / {len(scenes):02d}</div>
    </div>

    <div class="subtitle-stage">
      <div class="karaoke-text" id="karaokeBox">
        <span class="k-word active">PRESS</span>
        <span class="k-word active">PLAY</span>
        <span class="k-word">TO</span>
        <span class="k-word">PREVIEW</span>
      </div>
      <div class="broll-hint" id="brollHint">🎬 Visual: {scenes[0].get('visual_concept', 'Creator workspace') if scenes else ''}</div>
    </div>

    <div class="bottom-bar">
      <div class="progress-track" id="progressTrack">
        <div class="progress-fill" id="progressFill"></div>
      </div>
      <div class="controls-row">
        <button class="btn-play" id="playBtn">▶ PLAY PREVIEW</button>
        <div class="time-display" id="timeDisplay">00:00 / {int(total_duration // 60):02d}:{int(total_duration % 60):02d}</div>
      </div>
    </div>
  </div>
</div>

<script>
const events = {events_json};
const scenes = {scenes_json};
const totalDur = {total_duration};

let isPlaying = false;
let currentTime = 0;
let lastTimestamp = null;
let animationFrameId = null;

const playBtn = document.getElementById('playBtn');
const progressFill = document.getElementById('progressFill');
const progressTrack = document.getElementById('progressTrack');
const timeDisplay = document.getElementById('timeDisplay');
const sceneBadge = document.getElementById('sceneBadge');
const karaokeBox = document.getElementById('karaokeBox');
const brollHint = document.getElementById('brollHint');
const bgCanvas = document.getElementById('bgCanvas');

const bgGradients = [
  'radial-gradient(circle at 60% 40%, #064e3b 0%, #022c22 45%, #050b14 100%)',
  'radial-gradient(circle at 30% 70%, #0f766e 0%, #115e59 45%, #050b14 100%)',
  'radial-gradient(circle at 70% 30%, #1e3a8a 0%, #172554 45%, #050b14 100%)',
  'radial-gradient(circle at 50% 50%, #701a75 0%, #4a044e 45%, #050b14 100%)'
];

function formatTime(s) {{
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${{m.toString().padStart(2, '0')}}:${{sec.toString().padStart(2, '0')}}`;
}}

function updateDisplay() {{
  const pct = Math.min(100, (currentTime / totalDur) * 100);
  progressFill.style.width = pct + '%';
  timeDisplay.innerText = `${{formatTime(currentTime)}} / ${{formatTime(totalDur)}}`;

  let currentScene = scenes[0];
  for (let sc of scenes) {{
    if (currentTime >= sc.time_start && currentTime <= sc.time_end) {{
      currentScene = sc;
      break;
    }}
  }}

  if (currentScene) {{
    sceneBadge.innerText = `SCENE ${{currentScene.scene_idx.toString().padStart(2, '0')}} / ${{scenes.length.toString().padStart(2, '0')}}`;
    brollHint.innerText = `🎬 Visual: ${{currentScene.visual_concept || currentScene.broll_query || ''}}`;
    const gradIdx = (currentScene.scene_idx - 1) % bgGradients.length;
    bgCanvas.style.background = bgGradients[gradIdx];
  }}

  const activeWord = events.find(e => currentTime >= e.start && currentTime <= e.end);
  if (activeWord) {{
    const sceneWords = events.filter(e => e.scene_idx === activeWord.scene_idx);
    karaokeBox.innerHTML = sceneWords.map(w => {{
      const isAct = w === activeWord;
      return `<span class="k-word ${{isAct ? 'active' : ''}}">${{w.word}}</span>`;
    }}).join(' ');
  }}
}}

function step(timestamp) {{
  if (!lastTimestamp) lastTimestamp = timestamp;
  const delta = (timestamp - lastTimestamp) / 1000;
  lastTimestamp = timestamp;

  if (isPlaying) {{
    currentTime += delta;
    if (currentTime >= totalDur) {{
      currentTime = 0;
      isPlaying = false;
      playBtn.innerText = '▶ REPLAY';
    }}
    updateDisplay();
    animationFrameId = requestAnimationFrame(step);
  }}
}}

playBtn.addEventListener('click', () => {{
  isPlaying = !isPlaying;
  if (isPlaying) {{
    playBtn.innerText = '❚❚ PAUSE';
    lastTimestamp = null;
    animationFrameId = requestAnimationFrame(step);
  }} else {{
    playBtn.innerText = '▶ RESUME';
    cancelAnimationFrame(animationFrameId);
  }}
}});

progressTrack.addEventListener('click', (e) => {{
  const rect = progressTrack.getBoundingClientRect();
  const clickX = e.clientX - rect.left;
  const ratio = Math.max(0, Math.min(1, clickX / rect.width));
  currentTime = ratio * totalDur;
  updateDisplay();
}});

updateDisplay();
</script>

</body>
</html>
"""
    return html_code
