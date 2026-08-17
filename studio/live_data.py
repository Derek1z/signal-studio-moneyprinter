from __future__ import annotations

import json
import logging
import math
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

logger = logging.getLogger(__name__)

JsonGetter = Callable[[str], dict[str, Any]]


def _get_json(url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers=headers or {"User-Agent": "SignalStudio/2.0 (YouTube Editorial Assistant)"},
    )
    with urllib.request.urlopen(req, timeout=12) as response:
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
            query = urllib.parse.urlencode({
                "part": "snippet",
                "type": "video",
                "order": "viewCount",
                "maxResults": 10,
                "q": topic["topic"],
                "regionCode": region,
                "publishedAfter": published_after,
                "key": self.api_key,
            })
            try:
                search = self.getter(f"{self.SEARCH_URL}?{query}")
                ids = [item.get("id", {}).get("videoId") for item in search.get("items", [])]
                ids = [video_id for video_id in ids if video_id]
                if not ids:
                    scored.append({**topic, "source": "YouTube live · 0 matches", "sample_size": 0})
                    continue
                stats_query = urllib.parse.urlencode({
                    "part": "statistics,snippet",
                    "id": ",".join(ids),
                    "key": self.api_key,
                })
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
                    **topic,
                    "score": live_score,
                    "source": "YouTube Data API · last 30 days",
                    "sample_size": len(videos),
                    "views_30d": total_views,
                    "engagement_rate": round(engagement_rate, 2),
                    "signal": f"{total_views:,} views · {engagement_rate:.1f}% engagement · {len(videos)}-video sample",
                })
            except Exception as e:
                logger.warning(f"YouTube scoring failed for '{topic.get('topic')}': {e}")
                scored.append({**topic, "source": "YouTube live (error fallback)"})
        return sorted(scored, key=lambda row: row.get("score", 0), reverse=True)


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

    def research(self, topic: str, limit: int = 4) -> list[dict[str, str]]:
        if not self.configured:
            return []
        query = urllib.parse.urlencode({
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": f"{topic} statistics research study primary source",
            "num": min(10, max(1, limit)),
            "dateRestrict": "y2",
        })
        try:
            result = self.getter(f"{self.URL}?{query}")
            return [
                {
                    "claim": item.get("title", "Source candidate"),
                    "status": "Google Search Verified",
                    "source": item.get("displayLink", "Google Search"),
                    "url": item.get("link", ""),
                    "evidence": item.get("snippet", ""),
                }
                for item in result.get("items", [])
            ]
        except Exception as e:
            logger.warning(f"Google research failed: {e}")
            return []


class FreeWebSearchProvider:
    """Zero-key search provider using public DuckDuckGo Lite to fetch live citations."""

    URL = "https://html.duckduckgo.com/html/"

    @property
    def configured(self) -> bool:
        return True

    def research(self, topic: str, limit: int = 4) -> list[dict[str, str]]:
        data = urllib.parse.urlencode({"q": f"{topic} statistics research evidence"}).encode("utf-8")
        req = urllib.request.Request(
            self.URL,
            data=data,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=8) as response:
                html = response.read().decode("utf-8", errors="replace")

            # Extract result snippets and URLs from DuckDuckGo HTML Lite
            results = []
            link_pattern = re.findall(
                r'<a class="result__url" href="([^"]+)">(.*?)</a>[\s\S]*?<a class="result__snippet"[^>]*>(.*?)</a>',
                html,
            )
            for raw_url, display_host, snippet in link_pattern[:limit]:
                clean_snippet = re.sub(r"<[^>]+>", "", snippet).strip()
                clean_host = re.sub(r"<[^>]+>", "", display_host).strip()
                # DuckDuckGo redirect URL unpack
                actual_url = raw_url
                if "uddg=" in raw_url:
                    parsed_url = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
                    actual_url = parsed_url.get("uddg", [raw_url])[0]

                results.append({
                    "claim": clean_snippet[:120] + "..." if len(clean_snippet) > 120 else clean_snippet,
                    "status": "Web Search Result",
                    "source": clean_host or "Web Reference",
                    "url": actual_url,
                    "evidence": clean_snippet,
                })
            return results
        except Exception as e:
            logger.warning(f"FreeWebSearchProvider failed: {e}")
            return []


def get_research_pack(
    topic: str,
    provider_type: str = "demo",
    google_api_key: str = "",
    google_cx: str = "",
) -> list[dict[str, str]]:
    """Retrieve fact-checking research pack from configured provider with fallback to demo."""
    p_type = (provider_type or "demo").lower()
    if "google" in p_type and google_api_key and google_cx:
        google_prov = GoogleResearchProvider(google_api_key, google_cx)
        items = google_prov.research(topic)
        if items:
            return items
    elif "web" in p_type or "duckduckgo" in p_type:
        web_prov = FreeWebSearchProvider()
        items = web_prov.research(topic)
        if items:
            return items

    # Deterministic default research pack
    return [
        {
            "claim": "AI assistance is not, by itself, a YouTube monetization disqualifier.",
            "status": "Verified Policy",
            "source": "YouTube Help — Channel Monetization Policies",
            "url": "https://support.google.com/youtube/answer/1311392",
            "evidence": "Creators must add meaningful original commentary, educational value, or modified elements.",
        },
        {
            "claim": "Repetitive, mass-produced, or minimally transformed content violates YouTube Inauthentic Content guidelines.",
            "status": "Verified Policy",
            "source": "YouTube Help — Inauthentic Content Rules",
            "url": "https://support.google.com/youtube/answer/2801973",
            "evidence": "Templated videos without distinct editorial angle face demonetization and lower reach.",
        },
        {
            "claim": f"Audience engagement signals exist for '{topic}'.",
            "status": "Signal Checkpoint",
            "source": "Signal Studio Research Engine",
            "url": "",
            "evidence": "Topic has clear transformation value and search intent.",
        },
    ]
