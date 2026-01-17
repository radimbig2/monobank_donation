import asyncio
from pathlib import Path
from typing import Optional

from .url_parser import YouTubeURLParser
from .queue_manager import QueueManager, QueueItem
from .youtube_downloader import YouTubeDownloader
from .player import AudioPlayer


class YouTubePlayer:
    """Main YouTube player managing queue, downloads, and playback."""

    def __init__(self, queue_file: str = "youtube_queue.json", queue_manager: Optional[QueueManager] = None):
        self.parser = YouTubeURLParser()
        self.queue = queue_manager if queue_manager is not None else QueueManager(queue_file)
        self.downloader = YouTubeDownloader()
        self.player = AudioPlayer()

        self._current_index: Optional[int] = 0
        self._running = False
        self._playback_task: Optional[asyncio.Task] = None
        self._auto_play = False  # Don't auto-play on startup
        self._was_playing = False  # Track previous playback state

    async def add_from_comment(self, comment: str) -> bool:
        """
        Extract URL from comment and add to queue.
        Returns True if added, False otherwise.
        """
        print(f"[YouTubePlayer] add_from_comment called with: {comment[:100]}")

        url = self.parser.extract_url(comment)
        if not url:
            print("[YouTubePlayer] No YouTube URL found in comment")
            return False

        print(f"[YouTubePlayer] Extracted URL: {url}")

        # Check if already in queue
        for item in self.queue.get_all():
            if item.url == url:
                print("[YouTubePlayer] Already in queue")
                return False

        # Check duration
        print(f"[YouTubePlayer] Checking video length: {url}")
        is_valid = await self.downloader.is_valid_length(url)
        if not is_valid:
            print("[YouTubePlayer] Video is longer than 10 minutes")
            return False

        # Get info
        print(f"[YouTubePlayer] Getting video info...")
        info = await self.downloader.get_info(url)
        if not info:
            print("[YouTubePlayer] Could not get video info")
            return False

        title, duration = info
        print(f"[YouTubePlayer] Got info: {title} ({duration}s)")

        # Add to queue
        item = QueueItem(url=url, title=title, duration_sec=duration)
        self.queue.add(item)
        print(f"[YouTubePlayer] Added to queue: {title}")

        # Download if we have space (max 10 in cache)
        await self._download_next_items(max_downloads=10)

        return True

    async def _download_next_items(self, max_downloads: int = 10) -> None:
        """Download next items in queue up to max_downloads."""
        items = self.queue.get_all()
        downloaded = sum(1 for item in items if item.downloaded)

        print(f"[YouTubePlayer] Checking downloads: {len(items)} items, {downloaded} downloaded")

        for i, item in enumerate(items):
            if downloaded >= max_downloads:
                print(f"[YouTubePlayer] Max downloads ({max_downloads}) reached")
                break

            if not item.downloaded:
                # Get info first (update title and duration)
                info = await self.downloader.get_info(item.url)
                if info:
                    title, duration = info
                    self.queue.update_item_info(i, title=title, duration_sec=duration)
                    print(f"[YouTubePlayer] Downloading item {i+1}/{len(items)}: {title}")
                else:
                    print(f"[YouTubePlayer] Could not get info for: {item.url}")
                    continue

                video_id = self.parser.extract_video_id(item.url)
                if video_id:
                    self.queue.update_progress(i, 10)  # Start progress
                    file_path = await self.downloader.download(item.url, video_id)
                    if file_path:
                        self.queue.mark_downloaded(i, str(file_path))
                        self.queue.update_progress(i, 100)
                        downloaded += 1
                        print(f"[YouTubePlayer] Download complete at index {i}: {file_path}")

                        # Verify it was saved
                        current = self.get_current_track()
                        print(f"[YouTubePlayer] Current track after mark_downloaded: {current.title if current else 'None'}, downloaded={current.downloaded if current else 'N/A'}")
                    else:
                        print(f"[YouTubePlayer] Download failed for: {item.title}")
                        self.queue.update_progress(i, 0)
                else:
                    print(f"[YouTubePlayer] Could not extract video ID from: {item.url}")

    async def start(self) -> None:
        """Start playback loop."""
        if self._running:
            return

        self._running = True

        # Download existing items in queue
        print("[YouTubePlayer] Checking queue for items to download...")
        await self._download_next_items(max_downloads=10)

        self._playback_task = asyncio.create_task(self._playback_loop())
        print("[YouTubePlayer] Started")

    async def stop(self) -> None:
        """Stop playback."""
        self._running = False
        self._auto_play = False  # Disable auto-play when stopping
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
                is_playing = self.player.is_playing()

                # Check if playback just finished (was playing, now stopped)
                if self._was_playing and not is_playing:
                    # Track finished, auto-play next
                    print("[YouTubePlayer] Track finished, moving to next...")
                    next_item = self.queue.get_next()
                    if next_item:
                        if next_item.downloaded and next_item.file_path:
                            print(f"[YouTubePlayer] Playing: {next_item.title}")
                            self.player.play(Path(next_item.file_path))
                        else:
                            print(f"[YouTubePlayer] Waiting for download: {next_item.title}")
                            await asyncio.sleep(1)
                    else:
                        await asyncio.sleep(1)
                elif not is_playing and self._auto_play:
                    # Auto-play is enabled and nothing is playing
                    next_item = self.queue.get_next()
                    if next_item:
                        if next_item.downloaded and next_item.file_path:
                            print(f"[YouTubePlayer] Auto-playing: {next_item.title}")
                            self.player.play(Path(next_item.file_path))
                        else:
                            print(f"[YouTubePlayer] Waiting for download: {next_item.title}")
                            await asyncio.sleep(1)
                    else:
                        await asyncio.sleep(1)
                else:
                    # Either playing or user paused - just monitor
                    await asyncio.sleep(0.1)

                # Remember playback state for next iteration
                self._was_playing = is_playing

            except Exception as e:
                print(f"[YouTubePlayer] Playback error: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(1)

    def pause(self) -> bool:
        """Toggle play/pause."""
        print(f"[YouTubePlayer] Pause called. Is playing: {self.player.is_playing()}")
        if self.player.is_playing():
            # Currently playing - pause it
            result = self.player.pause()
            self._auto_play = False  # Stop auto-playing when paused
            print(f"[YouTubePlayer] Paused. Result: {result}")
            return result
        else:
            # Not playing - check if paused or fresh start
            print(f"[YouTubePlayer] Not playing. Is paused: {self.player.is_paused()}")
            self._auto_play = True  # Enable auto-play

            # Get current track and play it
            current = self.get_current_track()
            if current and current.downloaded and current.file_path:
                if self.player.is_paused():
                    # Was paused - resume from where we left off
                    print(f"[YouTubePlayer] Resuming: {current.title}")
                    result = self.player.resume()
                    print(f"[YouTubePlayer] Resume result: {result}")
                    return result
                else:
                    # Never played - start from beginning
                    print(f"[YouTubePlayer] Playing: {current.title}")
                    result = self.player.play(Path(current.file_path))
                    print(f"[YouTubePlayer] Play result: {result}")
                    return result
            else:
                print(f"[YouTubePlayer] Can't play - track not ready")
                if current:
                    print(f"  Downloaded: {current.downloaded}, File: {current.file_path}")
                return False

    def resume(self) -> bool:
        """Resume playback."""
        print(f"[YouTubePlayer] Resume called")
        self._auto_play = True  # Enable auto-play when resuming
        return self.player.resume()

    def next_track(self) -> None:
        """Skip to next track."""
        print(f"[YouTubePlayer] Next track called")
        self.player.stop()
        self._auto_play = True  # Enable auto-play when skipping to next

        # Remove current item from queue
        item = self.queue.remove(0)
        if item:
            print(f"[YouTubePlayer] Removed from queue: {item.title}")
            if item.file_path:
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
