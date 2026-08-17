from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def _find_ffmpeg() -> str | None:
    sys_ffmpeg = shutil.which("ffmpeg")
    if sys_ffmpeg:
        return sys_ffmpeg
    search_paths = [
        Path(__file__).parent.parent / "studio_outputs" / "bin" / "ffmpeg.exe",
        Path(__file__).parent.parent / "studio_outputs" / "test_run" / "bin" / "ffmpeg.exe",
    ]
    for p in search_paths:
        if p.exists() and p.stat().st_size > 1_000_000:
            return str(p.resolve())
    root_outputs = Path(__file__).parent.parent / "studio_outputs"
    for found in root_outputs.glob("**/ffmpeg.exe"):
        if found.stat().st_size > 1_000_000:
            return str(found.resolve())
    return None


def generate_themed_motion_clip(
    output_path: Path,
    scene_idx: int = 1,
    aspect_ratio: str = "16:9",
    duration_sec: int = 5,
    visual_theme: str = "cyber_matrix",
) -> bool:
    """Generate dynamic themed motion graphics video clips locally via FFmpeg."""
    ffmpeg_exe = _find_ffmpeg()
    if not ffmpeg_exe:
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if "9:16" in aspect_ratio:
        size = "720x1280"
    elif "1:1" in aspect_ratio:
        size = "1080x1080"
    else:
        size = "1280x720"

    theme_key = visual_theme.lower()
    if "cyber" in theme_key or "code" in theme_key:
        pattern = f"testsrc2=s={size}:r=24:d={duration_sec}"
        vf = "hue=H=2*PI*t/12:s=0.9,curves=green,eq=contrast=1.3:brightness=-0.05"
    elif "neon" in theme_key or "city" in theme_key:
        pattern = f"mandelbrot=s={size}:r=24:d={duration_sec}"
        vf = "hue=H=3*PI*t/8:s=1.0,eq=contrast=1.4:brightness=0.02"
    elif "space" in theme_key or "cosmos" in theme_key:
        pattern = f"sierpinski=s={size}:r=24:d={duration_sec}"
        vf = "hue=H=PI*t/10:s=0.7,eq=contrast=1.2:brightness=-0.1"
    elif "crypto" in theme_key or "finance" in theme_key:
        pattern = f"cellauto=s={size}:r=24:d={duration_sec}"
        vf = "scale={size},hue=s=0.8,curves=strong_contrast"
    else:
        # Kinetic Motion Default
        patterns = [
            f"mandelbrot=s={size}:r=24:d={duration_sec}",
            f"testsrc2=s={size}:r=24:d={duration_sec}",
            f"sierpinski=s={size}:r=24:d={duration_sec}",
        ]
        pattern = patterns[(scene_idx - 1) % len(patterns)]
        vf = "hue=H=2*PI*t/10:s=0.85,eq=contrast=1.25"

    cmd = [
        ffmpeg_exe, "-y",
        "-f", "lavfi",
        "-i", pattern,
        "-vf", vf,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-t", str(duration_sec),
        str(output_path.resolve().as_posix()),
    ]
    try:
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_path.exists() and output_path.stat().st_size > 1000
    except Exception as e:
        logger.warning(f"Themed B-roll generation failed: {e}")
        return False


def search_pexels_videos(
    query: str,
    api_key: str = "",
    orientation: str = "landscape",
    per_page: int = 5,
) -> list[dict[str, Any]]:
    clean_key = api_key.strip() or os.getenv("PEXELS_API_KEY", "")
    if not clean_key:
        return []

    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&per_page={per_page}&orientation={orientation}"
    req = urllib.request.Request(url, headers={"Authorization": clean_key, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = []
            for video in data.get("videos", []):
                video_files = video.get("video_files", [])
                hd_file = None
                for vf in video_files:
                    if vf.get("quality") == "hd" and vf.get("file_type") == "video/mp4":
                        hd_file = vf.get("link")
                        break
                if not hd_file and video_files:
                    hd_file = video_files[0].get("link")

                if hd_file:
                    results.append({
                        "id": f"pexels_{video.get('id')}",
                        "title": f"Pexels Video {video.get('id')}",
                        "url": hd_file,
                        "preview": video.get("image", ""),
                        "duration": video.get("duration", 6),
                    })
            return results
    except Exception as e:
        logger.warning(f"Pexels search failed for '{query}': {e}")
        return []


def download_video_clip(video_url: str, output_path: Path) -> bool:
    if output_path.exists() and output_path.stat().st_size > 10_000:
        return True

    output_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        video_url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response, open(output_path, "wb") as f:
            while chunk := response.read(64 * 1024):
                f.write(chunk)
        return True
    except Exception as e:
        logger.warning(f"Clip download failed for '{video_url}': {e}")
        return False


def get_clips_for_scenes(
    scenes: list[dict[str, Any]],
    pexels_api_key: str = "",
    aspect_ratio: str = "16:9",
    cache_dir: Path | None = None,
    visual_theme: str = "cyber_matrix",
) -> list[dict[str, Any]]:
    """Retrieve, generate, and cache distinct video clips for every storyboard scene with theme support."""
    out_cache = cache_dir or Path(__file__).parent.parent / "studio_outputs" / "stock_cache"
    out_cache.mkdir(parents=True, exist_ok=True)

    orientation = "portrait" if "9:16" in aspect_ratio else "landscape"
    matched_scenes = []

    for idx, sc in enumerate(scenes):
        scene_num = sc.get("scene_idx", idx + 1)
        query = sc.get("broll_query", "creator desk")
        clip_info = None

        if pexels_api_key.strip():
            live_clips = search_pexels_videos(query, api_key=pexels_api_key, orientation=orientation, per_page=3)
            if live_clips:
                clip_info = live_clips[idx % len(live_clips)]

        slug = re.sub(r"[^a-z0-9]+", "_", query.lower())[:20] or f"scene_{scene_num}"
        theme_slug = re.sub(r"[^a-z0-9]+", "_", visual_theme.lower())[:10]
        clip_file = out_cache / f"{theme_slug}_{slug}_{scene_num}.mp4"

        if clip_info:
            download_video_clip(clip_info["url"], clip_file)
        else:
            if not clip_file.exists() or clip_file.stat().st_size < 1000:
                generate_themed_motion_clip(
                    clip_file,
                    scene_idx=scene_num,
                    aspect_ratio=aspect_ratio,
                    duration_sec=sc.get("duration", 5),
                    visual_theme=visual_theme,
                )

        matched_scenes.append({
            **sc,
            "clip_id": f"scene_clip_{scene_num}",
            "clip_title": f"Scene {scene_num} ({visual_theme})",
            "clip_url": clip_info.get("url", "") if clip_info else "",
            "clip_preview": clip_info.get("preview", "") if clip_info else "",
            "clip_local_path": str(clip_file.resolve()) if clip_file.exists() and clip_file.stat().st_size > 1000 else "",
        })

    return matched_scenes
