from __future__ import annotations

import json
import math
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from urllib.parse import urlencode
from urllib.request import urlopen


JsonGetter = Callable[[str], dict[str, Any]]


def _get_json(url: str) -> dict[str, Any]:
    with urlopen(url, timeout=12) as response:  # nosec: URLs are fixed Google APIs
        return json.loads(response.read().decode("utf-8"))


class YouTubeTrendProvider:
    """Score candidate topics with recent public YouTube performance data."""

    SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
    VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"

    def __init__(self, api_key: str, getter: JsonGetter = _get_json):
        self.api_key = api_key.strip()
        self.getter = getter

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def score(self, topics: list[dict[str, Any]], region: str = "US") -> list[dict[str, Any]]:
        if not self.configured:
            return topics
        published_after = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat().replace("+00:00", "Z")
        scored = []
        for topic in topics:
            query = urlencode({
                "part": "snippet", "type": "video", "order": "viewCount",
                "maxResults": 12, "q": topic["topic"], "regionCode": region,
                "publishedAfter": published_after, "key": self.api_key,
            })
            search = self.getter(f"{self.SEARCH_URL}?{query}")
            ids = [item.get("id", {}).get("videoId") for item in search.get("items", [])]
            ids = [video_id for video_id in ids if video_id]
            if not ids:
                scored.append({**topic, "source": "YouTube live", "sample_size": 0})
                continue
            stats_query = urlencode({"part": "statistics,snippet", "id": ",".join(ids), "key": self.api_key})
            videos = self.getter(f"{self.VIDEOS_URL}?{stats_query}").get("items", [])
            views = [int(v.get("statistics", {}).get("viewCount", 0)) for v in videos]
            engagements = [
                int(v.get("statistics", {}).get("likeCount", 0)) + int(v.get("statistics", {}).get("commentCount", 0))
                for v in videos
            ]
            total_views = sum(views)
            engagement_rate = (sum(engagements) / total_views * 100) if total_views else 0
            velocity = min(100, math.log10(max(10, total_views)) * 18)
            opportunity = max(0, 100 - min(100, len(videos) * 5))
            live_score = round(0.55 * velocity + 0.25 * min(100, engagement_rate * 20) + 0.20 * opportunity)
            scored.append({
                **topic, "score": live_score, "source": "YouTube Data API · last 30 days",
                "sample_size": len(videos), "views_30d": total_views,
                "engagement_rate": round(engagement_rate, 2),
                "signal": f"{total_views:,} views · {engagement_rate:.1f}% engagement · {len(videos)}-video sample",
            })
        return sorted(scored, key=lambda row: row["score"], reverse=True)


class GoogleResearchProvider:
    """Retrieve source candidates from Google Programmable Search."""

    URL = "https://www.googleapis.com/customsearch/v1"

    def __init__(self, api_key: str, search_engine_id: str, getter: JsonGetter = _get_json):
        self.api_key = api_key.strip()
        self.search_engine_id = search_engine_id.strip()
        self.getter = getter

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.search_engine_id)

    def research(self, topic: str, limit: int = 5) -> list[dict[str, str]]:
        if not self.configured:
            return []
        query = urlencode({
            "key": self.api_key, "cx": self.search_engine_id,
            "q": f"{topic} evidence statistics research primary source",
            "num": min(10, max(1, limit)), "dateRestrict": "y2",
        })
        result = self.getter(f"{self.URL}?{query}")
        return [
            {
                "claim": item.get("title", "Source candidate"),
                "status": "AI-retrieved · review source",
                "source": item.get("displayLink", "Google Search"),
                "url": item.get("link", ""),
                "evidence": item.get("snippet", ""),
            }
            for item in result.get("items", [])
        ]

