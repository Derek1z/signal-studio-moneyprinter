from __future__ import annotations

import json
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Curated royalty-free sample stock videos for instant zero-key rendering
FALLBACK_STOCK_CLIPS = [
    {
        "id": "clip_desk_01",
        "title": "Creator Desk Workspace",
        "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
        "preview": "https://images.pexels.com/photos/3182773/pexels-photo-3182773.jpeg?auto=compress&cs=tinysrgb&w=600",
        "keywords": ["creator", "desk", "laptop", "typing", "editing", "workspace"],
    },
    {
        "id": "clip_tech_02",
        "title": "Abstract Data Flow",
        "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
        "preview": "https://images.pexels.com/photos/1181675/pexels-photo-1181675.jpeg?auto=compress&cs=tinysrgb&w=600",
        "keywords": ["data", "analytics", "dashboard", "ai", "technology", "diagram"],
    },
    {
        "id": "clip_focus_03",
        "title": "Deep Work Focus",
        "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
        "preview": "https://images.pexels.com/photos/3861969/pexels-photo-3861969.jpeg?auto=compress&cs=tinysrgb&w=600",
        "keywords": ["focus", "study", "research", "screen", "workflow", "checklist"],
    },
    {
        "id": "clip_success_04",
        "title": "Creative Achievement",
        "url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyBlazes.mp4",
        "preview": "https://images.pexels.com/photos/3184291/pexels-photo-3184291.jpeg?auto=compress&cs=tinysrgb&w=600",
        "keywords": ["success", "growth", "results", "leverage", "happy", "creator"],
    },
]


def search_pexels_videos(
    query: str,
    api_key: str = "",
    orientation: str = "landscape",
    per_page: int = 3,
) -> list[dict[str, Any]]:
    """Search Pexels API for royalty-free stock videos matching scene queries."""
    clean_key = api_key.strip() or os.getenv("PEXELS_API_KEY", "")
    if not clean_key:
        return []

    url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&per_page={per_page}&orientation={orientation}"
    req = urllib.request.Request(url, headers={"Authorization": clean_key, "User-Agent": "SignalStudio/2.2"})

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = []
            for video in data.get("videos", []):
                # Pick HD file (width approx 1920 or 1080)
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
    """Download video clip to local disk cache."""
    if output_path.exists() and output_path.stat().st_size > 100_000:
        return True

    output_path.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        video_url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as response, open(output_path, "wb") as f:
            while chunk := response.read(64 * 1024):
                f.write(chunk)
        return True
    except Exception as e:
        logger.warning(f"Failed to download clip '{video_url}': {e}")
        return False


def get_clips_for_scenes(
    scenes: list[dict[str, Any]],
    pexels_api_key: str = "",
    aspect_ratio: str = "16:9",
    cache_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Retrieve and cache matching video clips for all storyboard scenes."""
    out_cache = cache_dir or Path(__file__).parent.parent / "studio_outputs" / "stock_cache"
    out_cache.mkdir(parents=True, exist_ok=True)

    orientation = "portrait" if "9:16" in aspect_ratio else "landscape"
    matched_scenes = []

    for idx, sc in enumerate(scenes):
        query = sc.get("broll_query", "creator desk")
        clip_info = None

        # Try live Pexels API if key supplied
        if pexels_api_key.strip():
            live_clips = search_pexels_videos(query, api_key=pexels_api_key, orientation=orientation, per_page=1)
            if live_clips:
                clip_info = live_clips[0]

        # Fallback to curated library
        if not clip_info:
            clip_info = FALLBACK_STOCK_CLIPS[idx % len(FALLBACK_STOCK_CLIPS)]

        slug = re.sub(r"[^a-z0-9]+", "_", query.lower())[:24] or f"scene_{idx+1}"
        clip_file = out_cache / f"{slug}_{clip_info['id']}.mp4"

        # Download or verify presence
        download_video_clip(clip_info["url"], clip_file)

        matched_scenes.append({
            **sc,
            "clip_id": clip_info["id"],
            "clip_title": clip_info.get("title", f"Scene {idx+1} B-Roll"),
            "clip_url": clip_info["url"],
            "clip_preview": clip_info.get("preview", ""),
            "clip_local_path": str(clip_file) if clip_file.exists() else "",
        })

    return matched_scenes
