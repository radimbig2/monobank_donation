import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Tuple


class YouTubeDownloader:
    """Download YouTube videos using yt-dlp."""

    MAX_DURATION_SEC = 10 * 60  # 10 minutes
    CACHE_DIR = Path("./youtube_cache")

    def __init__(self):
        self.CACHE_DIR.mkdir(exist_ok=True)

    async def get_info(self, url: str) -> Optional[Tuple[str, int]]:
        """
        Get video info from YouTube.
        Returns: (title, duration_in_seconds) or None if error
        """
        try:
            print(f"[YouTubeDownloader] Getting info for: {url}")
            result = await asyncio.to_thread(
                subprocess.run,
                [
                    "yt-dlp",
                    "--dump-json",
                    "--no-warnings",
                    url
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            print(f"[YouTubeDownloader] yt-dlp return code: {result.returncode}")

            if result.returncode != 0:
                print(f"[YouTubeDownloader] yt-dlp error: {result.stderr}")
                return None

            import json
            data = json.loads(result.stdout)
            title = data.get("title", "Unknown")
            duration = data.get("duration", 0)
            print(f"[YouTubeDownloader] Got info: {title} ({duration}s)")
            return title, duration
        except Exception as e:
            print(f"[YouTubeDownloader] Error getting info: {e}")
            import traceback
            traceback.print_exc()

        return None

    async def download(self, url: str, video_id: str) -> Optional[Path]:
        """
        Download audio from YouTube video.
        Returns: Path to downloaded file or None if error/too long
        """
        try:
            # Get info first
            info = await self.get_info(url)
            if not info:
                print(f"[YouTubeDownloader] Could not get video info")
                return None

            title, duration = info

            # Check duration
            if duration > self.MAX_DURATION_SEC:
                print(f"[YouTubeDownloader] Video too long: {duration}s > {self.MAX_DURATION_SEC}s")
                return None

            # Download audio
            output_path = self.CACHE_DIR / f"{video_id}.mp3"

            if output_path.exists():
                print(f"[YouTubeDownloader] Already cached: {output_path}")
                return output_path

            print(f"[YouTubeDownloader] Downloading: {title} ({duration}s)")

            result = await asyncio.to_thread(
                subprocess.run,
                [
                    "yt-dlp",
                    "-f", "bestaudio",
                    "-x",
                    "--audio-format", "mp3",
                    "--audio-quality", "192",
                    "-o", str(output_path),
                    "--no-warnings",
                    url
                ],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0 and output_path.exists():
                print(f"[YouTubeDownloader] Downloaded: {output_path}")
                return output_path
            else:
                print(f"[YouTubeDownloader] Download failed: {result.stderr}")
                return None

        except Exception as e:
            print(f"[YouTubeDownloader] Error downloading: {e}")
            return None

    async def is_valid_length(self, url: str) -> bool:
        """Check if video is <= 10 minutes."""
        info = await self.get_info(url)
        if info:
            title, duration = info
            return duration <= self.MAX_DURATION_SEC
        return False

    def cleanup_cache(self, max_files: int = 10) -> None:
        """Remove oldest files if cache exceeds max_files."""
        files = sorted(
            self.CACHE_DIR.glob("*.mp3"),
            key=lambda f: f.stat().st_mtime
        )

        if len(files) > max_files:
            for f in files[:-max_files]:
                try:
                    f.unlink()
                    print(f"[YouTubeDownloader] Removed from cache: {f.name}")
                except Exception as e:
                    print(f"[YouTubeDownloader] Error removing cache: {e}")

    def get_cache_size(self) -> int:
        """Get number of files in cache."""
        return len(list(self.CACHE_DIR.glob("*.mp3")))
