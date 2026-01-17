import re
from typing import Optional


class YouTubeURLParser:
    """Parse YouTube URLs from text."""

    # Regex patterns for YouTube URLs
    PATTERNS = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)',
        r'https://youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'https://youtu\.be/([a-zA-Z0-9_-]+)',
    ]

    @staticmethod
    def extract_url(text: str) -> Optional[str]:
        """Extract YouTube URL from text (comment)."""
        if not text:
            return None

        for pattern in YouTubeURLParser.PATTERNS:
            match = re.search(pattern, text)
            if match:
                video_id = match.group(1)
                return f"https://www.youtube.com/watch?v={video_id}"

        return None

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        for pattern in YouTubeURLParser.PATTERNS:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
