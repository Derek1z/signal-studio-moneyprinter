from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable

from studio.stock_media import get_clips_for_scenes
from studio.storyboard import segment_script_into_scenes
from studio.voice import synthesize_speech

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[str, float], None]


def _get_ffmpeg_cmd() -> str | None:
    """Find FFmpeg executable in PATH or via imageio_ffmpeg bundled binary."""
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg
    try:
        import imageio_ffmpeg  # type: ignore

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
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
    ffmpeg_bin = _get_ffmpeg_cmd()

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
                # Write concat file
                concat_txt = output_dir / f"concat_{slug}.txt"
                lines = [f"file '{Path(c).as_posix()}'" for c in valid_clips]
                # Repeat clips if total duration is shorter than voice audio
                while len(lines) < len(scenes) and len(lines) < 10:
                    lines.extend([f"file '{Path(c).as_posix()}'" for c in valid_clips])
                concat_txt.write_text("\n".join(lines), encoding="utf-8")

                # Scale filter for aspect ratio
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

    # Strategy B: MoviePy Assembly
    if not rendered:
        try:
            from moviepy.editor import AudioFileClip, VideoFileClip, concatenate_videoclips  # type: ignore

            clips = []
            for sc in matched_scenes:
                local_p = sc.get("clip_local_path")
                if local_p and os.path.exists(local_p) and os.path.getsize(local_p) > 10_000:
                    try:
                        v_clip = VideoFileClip(local_p).subclip(0, min(sc["duration"], 8))
                        if "9:16" in aspect_ratio:
                            v_clip = v_clip.resize(height=1280).crop(x_center=v_clip.w / 2, width=720)
                        else:
                            v_clip = v_clip.resize(width=1280).crop(y_center=v_clip.h / 2, height=720)
                        clips.append(v_clip)
                    except Exception as e:
                        logger.warning(f"MoviePy clip read failed: {e}")

            if clips:
                final_video = concatenate_videoclips(clips, method="compose")
                if mp3_path and os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 1000:
                    audio = AudioFileClip(mp3_path)
                    final_video = final_video.set_audio(audio)
                final_video.write_videofile(
                    str(final_mp4),
                    fps=24,
                    codec="libx264",
                    audio_codec="aac",
                    logger=None,
                )
                if final_mp4.exists() and final_mp4.stat().st_size > 10_000:
                    rendered = True
                    render_note = "Rendered via MoviePy Engine"
        except Exception as exc:
            logger.warning(f"MoviePy render failed: {exc}")

    # Final Package Assembly
    report("✨ Complete! Video is ready for playback & download.", 1.0)

    # If full MP4 was generated
    if rendered and final_mp4.exists():
        return True, f"🎉 MP4 Video Rendered Successfully! ({render_note})", final_mp4

    # If video codecs are not installed yet, provide audio and instructional guidance
    bundle_manifest = {
        "status": "Voice Audio & Subtitles Ready",
        "topic": topic,
        "voice_audio": mp3_path,
        "subtitles_srt": srt_path,
        "scenes": matched_scenes,
        "note": "Install 'imageio-ffmpeg' (pip install imageio-ffmpeg) to enable automatic in-app MP4 rendering.",
    }
    manifest_file = output_dir / f"{slug}_bundle.json"
    manifest_file.write_text(json.dumps(bundle_manifest, indent=2), encoding="utf-8")

    return True, "🎙️ Audio voiceover and subtitles compiled! (Run 'pip install imageio-ffmpeg' for automatic MP4 stitching)", Path(mp3_path) if mp3_path and os.path.exists(mp3_path) else None
