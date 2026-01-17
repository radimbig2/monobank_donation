import re
from typing import Optional


class YouTubeURLParser:
    """Parse YouTube URLs from text."""

    # Regex patterns for YouTube URLs (includes youtube.com, youtu.be, and music.youtube.com)
    # Patterns are ordered to match most specific URLs first
    PATTERNS = [
        # music.youtube.com with optional parameters
        r'https://music\.youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'music\.youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        # youtube.com with optional parameters
        r'https://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        # youtu.be short links
        r'https://youtu\.be/([a-zA-Z0-9_-]+)',
        r'youtu\.be/([a-zA-Z0-9_-]+)',
    ]

    @staticmethod
    def extract_url(text: str) -> Optional[str]:
        """Extract YouTube URL from text (comment)."""
        if not text:
            print("[URLParser] Empty text")
            return None

        print(f"[URLParser] Parsing text: {text[:100]}")

        for pattern in YouTubeURLParser.PATTERNS:
            match = re.search(pattern, text)
            if match:
                video_id = match.group(1)
                url = f"https://www.youtube.com/watch?v={video_id}"
                print(f"[URLParser] Found video_id: {video_id}")
                print(f"[URLParser] Returning URL: {url}")
                return url

        print(f"[URLParser] No URL found in text")
        return None

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        for pattern in YouTubeURLParser.PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
