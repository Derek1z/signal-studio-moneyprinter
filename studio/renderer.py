from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Callable

from studio.stock_media import _detect_video_encoder, get_clips_for_scenes
from studio.storyboard import segment_script_into_scenes
from studio.voice import synthesize_speech

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, float], None]

FFMPEG_WIN64_ZIP_URL = "https://github.com/vot/ffbinaries-prebuilt/releases/download/v4.4.1/ffmpeg-4.4.1-win-64.zip"


def _ensure_ffmpeg(output_dir: Path | None = None) -> str | None:
    """Find or automatically download static portable FFmpeg executable."""
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg

    try:
        import imageio_ffmpeg  # type: ignore

        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception:
        pass

    exe_names = ["ffmpeg", "ffmpeg.exe"]
    search_dirs = [
        Path(__file__).parent.parent / "studio_outputs" / "bin",
        Path(__file__).parent.parent / "studio_outputs" / "test_run" / "bin",
    ]
    if output_dir:
        search_dirs.insert(0, Path(output_dir).resolve() / "bin")
        search_dirs.insert(1, Path(output_dir).resolve().parent / "bin")

    for s_dir in search_dirs:
        for name in exe_names:
            p = s_dir / name
            if p.exists() and p.stat().st_size > 100_000:
                return str(p.resolve())

    root_outputs = Path(__file__).parent.parent / "studio_outputs"
    for pattern in ["**/ffmpeg", "**/ffmpeg.exe"]:
        for found in root_outputs.glob(pattern):
            if found.is_file() and found.stat().st_size > 100_000:
                return str(found.resolve())

    # Only attempt Windows portable zip download on Windows
    if os.name == "nt":
        try:
            target_bin = (root_outputs / "bin").resolve()
            target_bin.mkdir(parents=True, exist_ok=True)
            zip_path = target_bin / "ffmpeg.zip"
            target_exe = target_bin / "ffmpeg.exe"

            req = urllib.request.Request(
                FFMPEG_WIN64_ZIP_URL,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
            with urllib.request.urlopen(req, timeout=30) as response, open(zip_path, "wb") as f:
                while chunk := response.read(128 * 1024):
                    f.write(chunk)

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extract("ffmpeg.exe", str(target_bin))

            if zip_path.exists():
                zip_path.unlink()

            if target_exe.exists():
                return str(target_exe)
        except Exception as e:
            logger.warning(f"Auto-download of portable FFmpeg failed: {e}")

    return None


def _detect_audio_encoder(ffmpeg_bin: str) -> str:
    """Dynamically determine the best supported AAC/MP3 audio encoder."""
    try:
        res = subprocess.run([ffmpeg_bin, "-encoders"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=8)
        output = res.stdout + res.stderr
        for candidate in ["aac", "libmp3lame"]:
            if candidate in output:
                return candidate
    except Exception:
        pass
    return "aac"


def render_video_pipeline(
    topic: str,
    script: str,
    settings: dict[str, Any],
    output_dir: Path,
    pexels_api_key: str = "",
    progress_callback: ProgressCallback | None = None,
) -> tuple[bool, str, Path | None]:
    """Execute complete in-house video generation: Voiceover Audio + Multi-Scene B-Roll + Subtitles + MP4 Rendering."""
    abs_out_dir = Path(output_dir).resolve()
    abs_out_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "_", topic.lower()).strip("_")[:32] or "studio_video"
    final_mp4 = abs_out_dir / f"{slug}_final.mp4"

    def report(msg: str, pct: float):
        if progress_callback:
            progress_callback(msg, pct)

    # 1. Synthesize Speech Audio (Edge-TTS / Native System / Synthetic)
    report("🎙️ Step 1/4: Synthesizing Spoken Voiceover Audio...", 0.20)
    voice_name = settings.get("voice_name", "en-US-JennyNeural-Female")
    voice_res = synthesize_speech(
        text=script,
        voice_name=voice_name,
        output_dir=abs_out_dir / "audio",
        rate_factor=float(settings.get("voice_rate", 1.0)),
    )
    mp3_path = voice_res.get("mp3_path")
    srt_path = voice_res.get("srt_path")
    audio_duration = max(4.0, float(voice_res.get("duration", 8.0)))

    # 2. Segment Storyboard & Scenes
    report("🎞️ Step 2/4: Segmenting Storyboard & Pacing Scenes...", 0.45)
    aspect_ratio = settings.get("video_aspect", "9:16")
    clip_dur = int(settings.get("video_clip_duration", 3))
    scenes = segment_script_into_scenes(script, target_clip_duration_sec=clip_dur)

    # 3. Acquire / Synthesize Dynamic B-Roll Video Clips
    report("📥 Step 3/4: Generating Dynamic Multi-Scene Video Backgrounds...", 0.70)
    visual_theme = settings.get("visual_theme", "cyber_matrix")
    matched_scenes = get_clips_for_scenes(
        scenes=scenes,
        pexels_api_key=pexels_api_key,
        aspect_ratio=aspect_ratio,
        cache_dir=abs_out_dir / "stock_cache",
        visual_theme=visual_theme,
    )

    # 4. Master Video Assembly (FFmpeg)
    report("🎬 Step 4/4: Stitching Multi-Scene Video & Voice Audio into MP4...", 0.90)

    rendered = False
    render_note = ""
    ffmpeg_bin = _ensure_ffmpeg(abs_out_dir)

    if ffmpeg_bin:
        v_encoder = _detect_video_encoder(ffmpeg_bin)
        a_encoder = _detect_audio_encoder(ffmpeg_bin)

        try:
            valid_clips = []
            for sc in matched_scenes:
                local_p = sc.get("clip_local_path")
                if local_p and os.path.exists(local_p) and os.path.getsize(local_p) > 1000:
                    valid_clips.append((str(Path(local_p).resolve()), float(sc.get("duration", clip_dur))))

            if "9:16" in aspect_ratio:
                vf_filter = "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1"
                res_w, res_h = 720, 1280
            elif "1:1" in aspect_ratio:
                vf_filter = "scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080,setsar=1"
                res_w, res_h = 1080, 1080
            else:
                vf_filter = "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,setsar=1"
                res_w, res_h = 1280, 720

            # Prepare subtitle filter if available
            has_subtitles = False
            vf_with_subs = vf_filter
            if srt_path and os.path.exists(srt_path) and os.path.getsize(srt_path) > 10:
                srt_escaped = str(Path(srt_path).resolve().as_posix()).replace(":", "\\:").replace("'", "\\'")
                vf_with_subs = f"{vf_filter},subtitles='{srt_escaped}':force_style='FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H000000,BorderStyle=3,Outline=2,Alignment=2,MarginV=30'"
                has_subtitles = True

            if valid_clips:
                concat_txt = abs_out_dir / f"concat_{slug}.txt"
                lines = []
                total_concat_dur = 0.0
                while total_concat_dur < (audio_duration + 5.0):
                    for clip_path, clip_dur_val in valid_clips:
                        lines.append(f"file '{Path(clip_path).resolve().as_posix()}'")
                        lines.append(f"duration {clip_dur_val}")
                        total_concat_dur += clip_dur_val
                # FFmpeg concat demuxer convention: last line repeats file without duration
                if valid_clips:
                    lines.append(f"file '{Path(valid_clips[0][0]).resolve().as_posix()}'")
                concat_txt.write_text("\n".join(lines), encoding="utf-8")

                input_args = [
                    "-f", "concat", "-safe", "0",
                    "-i", str(concat_txt.resolve().as_posix()),
                ]
            else:
                input_args = [
                    "-f", "lavfi",
                    "-i", f"testsrc2=s={res_w}x{res_h}:r=24",
                ]

            def _build_and_run_ffmpeg(active_vf: str) -> subprocess.CompletedProcess:
                cmd = [ffmpeg_bin, "-y"] + input_args
                if mp3_path and os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 500:
                    cmd.extend([
                        "-i", str(Path(mp3_path).resolve().as_posix()),
                        "-vf", active_vf,
                        "-c:v", v_encoder,
                        "-c:a", a_encoder,
                        "-b:a", "192k",
                        "-shortest",
                        "-pix_fmt", "yuv420p",
                    ])
                else:
                    cmd.extend([
                        "-vf", active_vf,
                        "-c:v", v_encoder,
                        "-pix_fmt", "yuv420p",
                        "-t", str(int(audio_duration)),
                    ])
                cmd.append(str(final_mp4.resolve().as_posix()))
                return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=90)

            # Try rendering with subtitles first
            res = _build_and_run_ffmpeg(vf_with_subs if has_subtitles else vf_filter)
            if not final_mp4.exists() or final_mp4.stat().st_size < 5000:
                # If subtitle filter failed (e.g. missing libass in ffmpeg build), render without subtitles
                logger.info(f"Subtitled render failed ({res.stderr[:80] if res.stderr else ''}), retrying standard render...")
                res = _build_and_run_ffmpeg(vf_filter)

            if final_mp4.exists() and final_mp4.stat().st_size > 5000:
                rendered = True
                render_note = f"Master Video Rendered ({aspect_ratio} · {v_encoder})"
        except Exception as exc:
            logger.warning(f"FFmpeg render pipeline failed: {exc}")

    report("✨ Master MP4 Video generation complete!", 1.0)

    if rendered and final_mp4.exists():
        return True, f"🎉 {aspect_ratio} Master Video Ready! ({render_note})", final_mp4

    if mp3_path and os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 500:
        return True, "🎙️ Audio voiceover and subtitles compiled!", Path(mp3_path)

    return False, "⚠️ Rendering failed to generate media output.", None

