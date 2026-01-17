import asyncio
from pathlib import Path
from typing import Optional

from .url_parser import YouTubeURLParser
from .queue_manager import QueueManager, QueueItem
from .youtube_downloader import YouTubeDownloader
from .player import AudioPlayer


class YouTubePlayer:
    """Main YouTube player managing queue, downloads, and playback."""

    def __init__(self, queue_file: str = "youtube_queue.json"):
        self.parser = YouTubeURLParser()
        self.queue = QueueManager(queue_file)
        self.downloader = YouTubeDownloader()
        self.player = AudioPlayer()

        self._current_index: Optional[int] = 0
        self._running = False
        self._playback_task: Optional[asyncio.Task] = None

    async def add_from_comment(self, comment: str) -> bool:
        """
        Extract URL from comment and add to queue.
        Returns True if added, False otherwise.
        """
        url = self.parser.extract_url(comment)
        if not url:
            print("[YouTubePlayer] No YouTube URL found in comment")
            return False

        # Check if already in queue
        for item in self.queue.get_all():
            if item.url == url:
                print("[YouTubePlayer] Already in queue")
                return False

        # Check duration
        is_valid = await self.downloader.is_valid_length(url)
        if not is_valid:
            print("[YouTubePlayer] Video is longer than 10 minutes")
            return False

        # Get info
        info = await self.downloader.get_info(url)
        if not info:
            print("[YouTubePlayer] Could not get video info")
            return False

        title, duration = info

        # Add to queue
        item = QueueItem(url=url, title=title, duration_sec=duration)
        self.queue.add(item)

        # Download if we have space (max 10 in cache)
        await self._download_next_items(max_downloads=10)

        return True

    async def _download_next_items(self, max_downloads: int = 10) -> None:
        """Download next items in queue up to max_downloads."""
        items = self.queue.get_all()
        downloaded = sum(1 for item in items if item.downloaded)

        for i, item in enumerate(items):
            if downloaded >= max_downloads:
                break

            if not item.downloaded:
                video_id = self.parser.extract_video_id(item.url)
                if video_id:
                    file_path = await self.downloader.download(item.url, video_id)
                    if file_path:
                        self.queue.mark_downloaded(i, str(file_path))
                        downloaded += 1

    async def start(self) -> None:
        """Start playback loop."""
        if self._running:
            return

        self._running = True
        self._playback_task = asyncio.create_task(self._playback_loop())
        print("[YouTubePlayer] Started")

    async def stop(self) -> None:
        """Stop playback."""
        self._running = False
        self.player.stop()

        if self._playback_task:
            self._playback_task.cancel()
            try:
                await self._playback_task
            except asyncio.CancelledError:
                pass
            self._playback_task = None

        print("[YouTubePlayer] Stopped")

    async def _playback_loop(self) -> None:
        """Main playback loop."""
        while self._running:
            try:
                if not self.player.is_playing():
                    # Play next item
                    next_item = self.queue.get_next()
                    if next_item and next_item.downloaded and next_item.file_path:
                        self.player.play(Path(next_item.file_path))
                    else:
                        await asyncio.sleep(1)
                else:
                    await asyncio.sleep(0.1)

            except Exception as e:
                print(f"[YouTubePlayer] Playback error: {e}")
                await asyncio.sleep(1)

    def pause(self) -> None:
        """Pause playback."""
        self.player.pause()

    def resume(self) -> None:
        """Resume playback."""
        self.player.resume()

    def next_track(self) -> None:
        """Skip to next track."""
        self.player.stop()
        # Remove current item from queue
        if self._current_index == 0 and self.queue.get_next():
            item = self.queue.remove(0)
            if item and item.file_path:
                try:
                    Path(item.file_path).unlink()
                    print(f"[YouTubePlayer] Deleted: {item.file_path}")
                except Exception as e:
                    print(f"[YouTubePlayer] Error deleting file: {e}")

    def set_volume(self, volume: float) -> None:
        """Set volume (0.0 to 1.0)."""
        self.player.set_volume(volume)

    def get_current_track(self) -> Optional[QueueItem]:
        """Get currently playing track."""
        return self.queue.get_next()

    def get_queue(self) -> list[QueueItem]:
        """Get all queued items."""
        return self.queue.get_all()

    def cleanup(self) -> None:
        """Cleanup resources."""
        self.player.cleanup()

    def is_playing(self) -> bool:
        """Check if music is playing."""
        return self.player.is_playing()
