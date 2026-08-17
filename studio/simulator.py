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
    width_css = "360px" if is_vertical else "100%"
    aspect_css = "9 / 16" if is_vertical else "16 / 9"
    max_height_css = "640px" if is_vertical else "480px"

    clean_title = html.escape(title or "Signal Studio Video Preview")

    # Build timed subtitle words list for client-side JS animation
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
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@700;800;900&family=DM+Sans:wght@700&display=swap');

* {{ box-sizing: border-box; margin: 0; padding: 0; user-select: none; }}
body {{ background: transparent; font-family: 'DM Sans', sans-serif; display: flex; justify-content: center; align-items: center; }}

.player-wrapper {{
  width: {width_css};
  max-width: 820px;
  background: #090e0c;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0,0,0,0.5);
  border: 1px solid rgba(255,255,255,0.1);
  position: relative;
}}

.viewport {{
  width: 100%;
  aspect-ratio: {aspect_css};
  max-height: {max_height_css};
  position: relative;
  overflow: hidden;
  background: #0d1713;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}}

/* Dynamic Ambient Video Canvas */
.bg-canvas {{
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background: radial-gradient(circle at 60% 40%, #1a5641 0%, #0d281e 50%, #07130f 100%);
  transition: all 0.6s ease;
  z-index: 1;
}}

.glow-orb {{
  position: absolute;
  width: 300px; height: 300px;
  border-radius: 50%;
  background: #d2f866;
  filter: blur(90px);
  opacity: 0.15;
  top: 20%; right: 10%;
  animation: pulse 4s infinite alternate ease-in-out;
  z-index: 2;
}}

@keyframes pulse {{
  0% {{ transform: scale(0.9) translate(0, 0); opacity: 0.12; }}
  100% {{ transform: scale(1.15) translate(-20px, 20px); opacity: 0.22; }}
}}

/* Top Overlay Badges */
.top-bar {{
  position: relative;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
}}

.brand-pill {{
  background: rgba(0,0,0,0.5);
  backdrop-filter: blur(8px);
  border: 1px solid rgba(210, 248, 102, 0.4);
  padding: 4px 10px;
  border-radius: 99px;
  font-size: 11px;
  font-weight: 800;
  color: #d2f866;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}

.scene-pill {{
  background: rgba(0,0,0,0.6);
  backdrop-filter: blur(8px);
  padding: 4px 12px;
  border-radius: 99px;
  font-size: 11px;
  font-weight: 700;
  color: #ffffff;
}}

/* Center Subtitle Karaoke Stage */
.subtitle-stage {{
  position: relative;
  z-index: 10;
  padding: 20px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 140px;
}}

.karaoke-text {{
  font-family: 'Manrope', Impact, sans-serif;
  font-weight: 900;
  font-size: {"32px" if is_vertical else "38px"};
  line-height: 1.15;
  color: #ffffff;
  text-transform: uppercase;
  text-shadow: 0 4px 14px rgba(0,0,0,0.9), 0 0 2px #000;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}}

.k-word {{
  display: inline-block;
  transition: all 0.12s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}}

.k-word.active {{
  color: #d2f866;
  transform: scale(1.18);
  text-shadow: 0 0 20px rgba(210, 248, 102, 0.6), 0 4px 12px #000;
}}

.broll-hint {{
  margin-top: 10px;
  font-size: 12px;
  color: rgba(255,255,255,0.6);
  background: rgba(0,0,0,0.4);
  padding: 3px 10px;
  border-radius: 6px;
}}

/* Bottom Controller Bar */
.bottom-bar {{
  position: relative;
  z-index: 10;
  background: rgba(9, 14, 12, 0.85);
  backdrop-filter: blur(12px);
  padding: 12px 18px;
  border-top: 1px solid rgba(255,255,255,0.08);
}}

.progress-track {{
  width: 100%;
  height: 6px;
  background: rgba(255,255,255,0.15);
  border-radius: 3px;
  cursor: pointer;
  position: relative;
  margin-bottom: 10px;
}}

.progress-fill {{
  height: 100%;
  width: 0%;
  background: #d2f866;
  border-radius: 3px;
  transition: width 0.05s linear;
}}

.controls-row {{
  display: flex;
  align-items: center;
  justify-content: space-between;
}}

.btn-play {{
  background: #d2f866;
  border: none;
  color: #091a13;
  font-weight: 800;
  font-size: 13px;
  padding: 6px 16px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}}

.btn-play:hover {{
  background: #ffffff;
  transform: scale(1.04);
}}

.time-display {{
  font-size: 12px;
  font-weight: 700;
  color: #a1b0a8;
  font-family: monospace;
}}
</style>
</head>
<body>

<div class="player-wrapper">
  <div class="viewport" id="viewport">
    <div class="bg-canvas" id="bgCanvas"></div>
    <div class="glow-orb"></div>

    <div class="top-bar">
      <div class="brand-pill">◉ SIGNAL LIVE</div>
      <div class="scene-pill" id="sceneBadge">SCENE 01 / {len(scenes):02d}</div>
    </div>

    <div class="subtitle-stage">
      <div class="karaoke-text" id="karaokeBox">
        <span class="k-word active">PRESS</span>
        <span class="k-word active">PLAY</span>
        <span class="k-word">TO</span>
        <span class="k-word">PREVIEW</span>
      </div>
      <div class="broll-hint" id="brollHint">🎬 Visual: {scenes[0].get('visual_concept', 'Creator desk') if scenes else ''}</div>
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
  'radial-gradient(circle at 60% 40%, #1a5641 0%, #0d281e 50%, #07130f 100%)',
  'radial-gradient(circle at 30% 70%, #0369a1 0%, #082f49 50%, #050e14 100%)',
  'radial-gradient(circle at 70% 30%, #b45309 0%, #451a03 50%, #120702 100%)',
  'radial-gradient(circle at 50% 50%, #7c2d12 0%, #3f1207 50%, #0e0503 100%)'
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

  // Find active scene
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

  // Find active words in current window
  const activeWord = events.find(e => currentTime >= e.start && currentTime <= e.end);
  if (activeWord) {{
    // Get adjacent words in same scene
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
