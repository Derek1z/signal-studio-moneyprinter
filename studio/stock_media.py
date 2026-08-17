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

# Reliable royalty-free open-access sample stock video clips with working direct URLs
CURATED_STOCK_LIBRARY = [
    {
        "id": "clip_nature_01",
        "title": "Macro Flow Nature Timelapse",
        "category": "lifestyle",
        "url": "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4",
        "preview": "https://images.unsplash.com/photo-1518531933037-91b2f5f229cc?w=600&auto=format&fit=crop&q=60",
        "keywords": ["creator", "nature", "focus", "lifestyle", "time", "calm"],
    },
    {
        "id": "clip_tech_02",
        "title": "Abstract Data Movement",
        "category": "tech",
        "url": "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4",
        "preview": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=600&auto=format&fit=crop&q=60",
        "keywords": ["code", "ai", "terminal", "algorithm", "python", "developer", "system"],
    },
]


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


def generate_motion_broll_clip(
    output_path: Path,
    scene_idx: int = 1,
    aspect_ratio: str = "16:9",
    duration_sec: int = 5,
) -> bool:
    """Generate dynamic, high-energy animated motion graphics video clips locally via FFmpeg."""
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

    # Motion patterns to vary across scenes
    patterns = [
        f"mandelbrot=s={size}:r=24:d={duration_sec}",
        f"testsrc2=s={size}:r=24:d={duration_sec}",
        f"sierpinski=s={size}:r=24:d={duration_sec}",
        f"cellauto=s={size}:r=24:d={duration_sec}",
        f"color=c=0x0a1e16:s={size}:r=24:d={duration_sec}",
    ]

    pat = patterns[(scene_idx - 1) % len(patterns)]
    cmd = [
        ffmpeg_exe, "-y",
        "-f", "lavfi",
        "-i", pat,
        "-vf", "hue=H=2*PI*t/10:s=0.8,eq=contrast=1.2:brightness=-0.05",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-t", str(duration_sec),
        str(output_path.resolve().as_posix()),
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_path.exists() and output_path.stat().st_size > 1000
    except Exception as e:
        logger.warning(f"Motion B-roll generation failed: {e}")
        return False


def search_pexels_videos(
    query: str,
    api_key: str = "",
    orientation: str = "landscape",
    per_page: int = 5,
) -> list[dict[str, Any]]:
    """Search Pexels API for royalty-free stock videos matching scene queries."""
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
    """Download video clip to local disk cache with browser headers."""
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
) -> list[dict[str, Any]]:
    """Retrieve, generate, and cache distinct video clips for every storyboard scene."""
    out_cache = cache_dir or Path(__file__).parent.parent / "studio_outputs" / "stock_cache"
    out_cache.mkdir(parents=True, exist_ok=True)

    orientation = "portrait" if "9:16" in aspect_ratio else "landscape"
    matched_scenes = []

    for idx, sc in enumerate(scenes):
        scene_num = sc.get("scene_idx", idx + 1)
        query = sc.get("broll_query", "creator desk")
        clip_info = None

        # 1. Try Pexels Live Search if API Key is configured
        if pexels_api_key.strip():
            live_clips = search_pexels_videos(query, api_key=pexels_api_key, orientation=orientation, per_page=3)
            if live_clips:
                clip_info = live_clips[idx % len(live_clips)]

        slug = re.sub(r"[^a-z0-9]+", "_", query.lower())[:20] or f"scene_{scene_num}"
        clip_file = out_cache / f"{slug}_{scene_num}.mp4"

        # 2. Download from Pexels or generate dynamic motion graphics clip locally
        if clip_info:
            download_video_clip(clip_info["url"], clip_file)
        else:
            if not clip_file.exists() or clip_file.stat().st_size < 1000:
                generate_motion_broll_clip(clip_file, scene_idx=scene_num, aspect_ratio=aspect_ratio, duration_sec=sc.get("duration", 5))

        matched_scenes.append({
            **sc,
            "clip_id": f"scene_clip_{scene_num}",
            "clip_title": f"Scene {scene_num} Motion B-Roll",
            "clip_url": clip_info.get("url", "") if clip_info else "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4",
            "clip_preview": clip_info.get("preview", "") if clip_info else "",
            "clip_local_path": str(clip_file.resolve()) if clip_file.exists() and clip_file.stat().st_size > 1000 else "",
        })

    return matched_scenes
