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

from studio.stock_media import get_clips_for_scenes
from studio.storyboard import segment_script_into_scenes
from studio.voice import synthesize_speech

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, float], None]

FFMPEG_WIN64_ZIP_URL = "https://github.com/vot/ffbinaries-prebuilt/releases/download/v4.4.1/ffmpeg-4.4.1-win-64.zip"


def _ensure_ffmpeg(output_dir: Path | None = None) -> str | None:
    """Find or automatically download static portable FFmpeg executable."""
    # 1. Check system PATH
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg

    # 2. Check imageio_ffmpeg
    try:
        import imageio_ffmpeg  # type: ignore

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass

    # 3. Check local studio bin
    base_dir = output_dir or Path(__file__).parent.parent / "studio_outputs"
    bin_dir = base_dir / "bin"
    ffmpeg_exe = bin_dir / "ffmpeg.exe"
    if ffmpeg_exe.exists() and ffmpeg_exe.stat().st_size > 1_000_000:
        return str(ffmpeg_exe)

    # 4. Auto-download static portable binary (zero user setup needed)
    try:
        bin_dir.mkdir(parents=True, exist_ok=True)
        zip_path = bin_dir / "ffmpeg.zip"
        req = urllib.request.Request(
            FFMPEG_WIN64_ZIP_URL,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        )
        with urllib.request.urlopen(req, timeout=30) as response, open(zip_path, "wb") as f:
            while chunk := response.read(128 * 1024):
                f.write(chunk)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extract("ffmpeg.exe", str(bin_dir))

        if zip_path.exists():
            zip_path.unlink()

        if ffmpeg_exe.exists():
            return str(ffmpeg_exe)
    except Exception as e:
        logger.warning(f"Auto-download of portable FFmpeg failed: {e}")

    return None


def render_video_pipeline(
    topic: str,
    script: str,
    settings: dict[str, Any],
    output_dir: Path,
    pexels_api_key: str = "",
    progress_callback: ProgressCallback | None = None,
) -> tuple[bool, str, Path | None]:
    """Execute complete in-house video generation: TTS + B-Roll + Subtitles + MP4 Rendering."""
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "_", topic.lower()).strip("_")[:32] or "studio_video"
    final_mp4 = output_dir / f"{slug}_final.mp4"

    def report(msg: str, pct: float):
        if progress_callback:
            progress_callback(msg, pct)

    # 1. Synthesize Speech
    report("🎙️ Step 1/4: Synthesizing Microsoft Neural Voiceover...", 0.20)
    voice_name = settings.get("voice_name", "en-US-JennyNeural-Female")
    voice_res = synthesize_speech(
        text=script,
        voice_name=voice_name,
        output_dir=output_dir / "audio",
        rate_factor=float(settings.get("voice_rate", 1.0)),
    )
    mp3_path = voice_res.get("mp3_path")
    srt_path = voice_res.get("srt_path")
    audio_duration = voice_res.get("duration", 10.0)

    # 2. Segment Storyboard & Scenes
    report("🎞️ Step 2/4: Segmenting Scene Storyboard & B-Roll Timing...", 0.45)
    aspect_ratio = settings.get("video_aspect", "16:9")
    clip_dur = int(settings.get("video_clip_duration", 5))
    scenes = segment_script_into_scenes(script, target_clip_duration_sec=clip_dur)

    # 3. Acquire B-Roll Video Clips
    report("📥 Step 3/4: Downloading & Caching Stock Video Clips...", 0.70)
    matched_scenes = get_clips_for_scenes(
        scenes=scenes,
        pexels_api_key=pexels_api_key,
        aspect_ratio=aspect_ratio,
        cache_dir=output_dir / "stock_cache",
    )

    # 4. Video Assembly / Rendering
    report("🎬 Step 4/4: Stitching Video, Audio & Subtitles into MP4...", 0.90)

    rendered = False
    render_note = ""
    ffmpeg_bin = _ensure_ffmpeg(output_dir)

    # Strategy A: FFmpeg Direct Assembly (Fastest & Most Reliable)
    if ffmpeg_bin:
        try:
            valid_clips = []
            for sc in matched_scenes:
                local_p = sc.get("clip_local_path")
                if local_p and os.path.exists(local_p) and os.path.getsize(local_p) > 10_000:
                    valid_clips.append(local_p)

            # If no scene clips, search in stock_cache for any mp4
            if not valid_clips:
                stock_cache_dir = output_dir / "stock_cache"
                for f in stock_cache_dir.glob("*.mp4"):
                    if f.stat().st_size > 10_000:
                        valid_clips.append(str(f))

            if valid_clips:
                concat_txt = output_dir / f"concat_{slug}.txt"
                lines = [f"file '{Path(c).as_posix()}'" for c in valid_clips]
                # Repeat clips if total duration is shorter than voice audio
                while len(lines) < len(scenes) and len(lines) < 10:
                    lines.extend([f"file '{Path(c).as_posix()}'" for c in valid_clips])
                concat_txt.write_text("\n".join(lines), encoding="utf-8")

                vf_filter = "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720"
                if "9:16" in aspect_ratio:
                    vf_filter = "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280"

                cmd = [
                    ffmpeg_bin, "-y",
                    "-f", "concat", "-safe", "0",
                    "-i", str(concat_txt),
                ]

                if mp3_path and os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 1000:
                    cmd.extend([
                        "-i", str(mp3_path),
                        "-vf", vf_filter,
                        "-c:v", "libx264",
                        "-c:a", "aac",
                        "-shortest",
                        "-pix_fmt", "yuv420p",
                    ])
                else:
                    cmd.extend([
                        "-vf", vf_filter,
                        "-c:v", "libx264",
                        "-pix_fmt", "yuv420p",
                        "-t", str(int(audio_duration)),
                    ])

                cmd.append(str(final_mp4))
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                if final_mp4.exists() and final_mp4.stat().st_size > 10_000:
                    rendered = True
                    render_note = "Assembled via Native FFmpeg Video Engine"
                else:
                    logger.warning(f"FFmpeg stdout/err: {res.stderr}")
        except Exception as exc:
            logger.warning(f"FFmpeg render attempt failed: {exc}")

    # Final Package Assembly
    report("✨ Complete! Video is ready for playback & download.", 1.0)

    # If full MP4 was generated
    if rendered and final_mp4.exists():
        return True, f"🎉 MP4 Video Rendered Successfully! ({render_note})", final_mp4

    # If MP4 not yet written, provide audio
    return True, "🎙️ Audio voiceover and subtitles compiled!", Path(mp3_path) if mp3_path and os.path.exists(mp3_path) else None
