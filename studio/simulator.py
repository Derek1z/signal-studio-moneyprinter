from __future__ import annotations

import html
import json
from typing import Any


def render_live_video_simulator(
    scenes: list[dict[str, Any]],
    title: str = "Video Preview",
    aspect_ratio: str = "16:9",
    subtitle_style: str = "hormozi",
    audio_url: str = "",
) -> str:
    """Generate an interactive HTML5/JavaScript player with synchronized animated karaoke subtitles and real background video clips."""
    is_vertical = "9:16" in aspect_ratio
    is_square = "1:1" in aspect_ratio

    if is_vertical:
        width_css = "320px"
        aspect_css = "9 / 16"
        max_height_css = "560px"
        phone_border_css = "border: 8px solid #1e293b; border-radius: 36px; box-shadow: 0 25px 60px rgba(0,0,0,0.8), 0 0 0 1px rgba(255,255,255,0.1);"
        notch_html = '<div class="phone-notch"><div class="speaker"></div><div class="camera"></div></div>'
    elif is_square:
        width_css = "440px"
        aspect_css = "1 / 1"
        max_height_css = "440px"
        phone_border_css = "border: 1px solid rgba(255,255,255,0.15); border-radius: 18px;"
        notch_html = ""
    else:
        width_css = "100%"
        aspect_css = "16 / 9"
        max_height_css = "440px"
        phone_border_css = "border: 1px solid rgba(255,255,255,0.15); border-radius: 18px;"
        notch_html = ""

    clean_title = html.escape(title or "Signal Studio Video Preview")

    style_key = (subtitle_style or "hormozi").lower()
    if "mrbeast" in style_key:
        active_color = "#ffffff"
        active_bg = "#dc2626"
        active_glow = "rgba(220, 38, 38, 0.8)"
    elif "cyber" in style_key:
        active_color = "#030712"
        active_bg = "#06b6d4"
        active_glow = "rgba(6, 182, 212, 0.8)"
    elif "minimal" in style_key:
        active_color = "#000000"
        active_bg = "#ffffff"
        active_glow = "rgba(255, 255, 255, 0.4)"
    else:
        active_color = "#04100c"
        active_bg = "#10b981"
        active_glow = "rgba(16, 185, 129, 0.8)"

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
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@700;800;900&family=Outfit:wght@800;900&display=swap');

* {{ box-sizing: border-box; margin: 0; padding: 0; user-select: none; }}
body {{ background: transparent; font-family: 'Plus Jakarta Sans', sans-serif; display: flex; justify-content: center; align-items: center; padding: 6px; }}

.player-wrapper {{
  width: {width_css};
  max-width: 820px;
  background: #090d16;
  overflow: hidden;
  {phone_border_css}
  position: relative;
}}

.phone-notch {{
  position: absolute;
  top: 6px;
  left: 50%;
  transform: translateX(-50%);
  width: 90px;
  height: 18px;
  background: #1e293b;
  border-radius: 0 0 12px 12px;
  z-index: 25;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}}

.phone-notch .speaker {{
  width: 32px;
  height: 4px;
  background: #334155;
  border-radius: 2px;
}}

.phone-notch .camera {{
  width: 6px;
  height: 6px;
  background: #0f172a;
  border-radius: 50%;
  border: 1px solid #334155;
}}

.viewport {{
  width: 100%;
  aspect-ratio: {aspect_css};
  max-height: {max_height_css};
  position: relative;
  overflow: hidden;
  background: #060911;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}}

/* Real Background Video Player with Ambient Overlay */
.bg-video {{
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  object-fit: cover;
  z-index: 1;
  opacity: 0.65;
  filter: saturate(1.2) contrast(1.1);
  transition: opacity 0.4s ease;
}}

.bg-overlay {{
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background: linear-gradient(180deg, rgba(6,9,17,0.4) 0%, rgba(6,9,17,0.1) 40%, rgba(6,9,17,0.75) 100%);
  z-index: 2;
}}

.glow-orb {{
  position: absolute;
  width: 260px; height: 260px;
  border-radius: 50%;
  background: {active_bg};
  filter: blur(95px);
  opacity: 0.22;
  top: 20%; right: 10%;
  animation: pulse 4s infinite alternate ease-in-out;
  z-index: 2;
}}

@keyframes pulse {{
  0% {{ transform: scale(0.9) translate(0, 0); opacity: 0.16; }}
  100% {{ transform: scale(1.2) translate(-20px, 20px); opacity: 0.32; }}
}}

.equalizer-bar-container {{
  position: absolute;
  bottom: 60px;
  left: 18px;
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 22px;
  z-index: 5;
  opacity: 0.6;
}}

.eq-bar {{
  width: 3px;
  background: {active_bg};
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

.top-bar {{
  position: relative;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: {"24px 16px 10px" if is_vertical else "14px 18px"};
}}

.brand-pill {{
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  padding: 3px 10px;
  border-radius: 99px;
  font-size: 10px;
  font-weight: 800;
  color: {active_bg};
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}

.scene-pill {{
  background: rgba(15, 23, 42, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  padding: 3px 10px;
  border-radius: 99px;
  font-size: 10px;
  font-weight: 700;
  color: #f8fafc;
}}

.subtitle-stage {{
  position: relative;
  z-index: 10;
  padding: 16px 18px;
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
  font-size: {"22px" if is_vertical else "30px"};
  line-height: 1.2;
  color: #ffffff;
  text-transform: uppercase;
  text-shadow: 0 4px 18px rgba(0,0,0,0.95), 0 0 4px #000;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 6px;
}}

.k-word {{
  display: inline-block;
  padding: 2px 6px;
  border-radius: 6px;
  transition: all 0.12s cubic-bezier(0.34, 1.56, 0.64, 1);
}}

.k-word.active {{
  color: {active_color};
  background: {active_bg};
  transform: scale(1.16) translateY(-2px);
  box-shadow: 0 0 25px {active_glow};
  text-shadow: none;
}}

.broll-hint {{
  margin-top: 12px;
  font-size: 11px;
  font-weight: 700;
  color: #e2e8f0;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(8px);
  padding: 4px 12px;
  border-radius: 99px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  max-width: 90%;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}}

.bottom-bar {{
  position: relative;
  z-index: 10;
  background: rgba(9, 13, 22, 0.92);
  backdrop-filter: blur(16px);
  padding: 10px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
}}

.progress-track {{
  width: 100%;
  height: 5px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 3px;
  cursor: pointer;
  position: relative;
  margin-bottom: 8px;
  overflow: hidden;
}}

.progress-fill {{
  height: 100%;
  width: 0%;
  background: {active_bg};
  border-radius: 3px;
  transition: width 0.04s linear;
}}

.controls-row {{
  display: flex;
  align-items: center;
  justify-content: space-between;
}}

.btn-play {{
  background: {active_bg};
  border: none;
  color: {active_color};
  font-weight: 800;
  font-size: 11px;
  letter-spacing: 0.04em;
  padding: 6px 14px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 0 15px {active_glow};
}}

.btn-play:hover {{
  filter: brightness(1.15);
  transform: scale(1.04);
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
  {notch_html}
  <div class="viewport" id="viewport">
    <video class="bg-video" id="bgVideo" autoplay loop muted playsinline>
      <source src="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4" type="video/mp4">
    </video>
    <div class="bg-overlay"></div>
    <div class="glow-orb"></div>

    <div class="equalizer-bar-container">
      <div class="eq-bar"></div>
      <div class="eq-bar"></div>
      <div class="eq-bar"></div>
      <div class="eq-bar"></div>
      <div class="eq-bar"></div>
    </div>

    <div class="top-bar">
      <div class="brand-pill">{aspect_ratio} FORMAT</div>
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
let currentSceneIdx = -1;

const playBtn = document.getElementById('playBtn');
const progressFill = document.getElementById('progressFill');
const progressTrack = document.getElementById('progressTrack');
const timeDisplay = document.getElementById('timeDisplay');
const sceneBadge = document.getElementById('sceneBadge');
const karaokeBox = document.getElementById('karaokeBox');
const brollHint = document.getElementById('brollHint');
const bgVideo = document.getElementById('bgVideo');

const videoClips = [
  'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
  'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyBlazes.mp4',
  'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerMeltdowns.mp4',
  'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4',
  'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4',
  'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4'
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

  if (currentScene && currentScene.scene_idx !== currentSceneIdx) {{
    currentSceneIdx = currentScene.scene_idx;
    sceneBadge.innerText = `SCENE ${{currentScene.scene_idx.toString().padStart(2, '0')}} / ${{scenes.length.toString().padStart(2, '0')}}`;
    brollHint.innerText = `🎬 Visual: ${{currentScene.visual_concept || currentScene.broll_query || ''}}`;
    
    // Switch background video on scene change
    const clipIdx = (currentScene.scene_idx - 1) % videoClips.length;
    const newSrc = currentScene.clip_url || videoClips[clipIdx];
    if (bgVideo.currentSrc !== newSrc) {{
      bgVideo.src = newSrc;
      bgVideo.play().catch(e => console.log('Video play policy: ', e));
    }}
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
    bgVideo.play().catch(e => {{}});
    animationFrameId = requestAnimationFrame(step);
  }} else {{
    playBtn.innerText = '▶ RESUME';
    bgVideo.pause();
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
