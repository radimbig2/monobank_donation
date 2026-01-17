import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.web_host import WebHost
    from src.media_player import MediaPlayer
    from src.config import Config


@dataclass
class Donation:
    amount: int  # in kopecks (1 UAH = 100 kopecks)
    currency: str = "UAH"
    comment: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)
    donor_name: str | None = None

    @property
    def amount_uah(self) -> float:
        """Get amount in UAH."""
        return self.amount / 100

    def __str__(self) -> str:
        name = self.donor_name or "Anonymous"
        return f"{name}: {self.amount_uah:.2f} {self.currency}"


class NotificationService:
    def __init__(
        self,
        web_host: "WebHost",
        media_player: "MediaPlayer",
        config: "Config",
    ):
        self._web_host = web_host
        self._media_player = media_player
        self._config = config

        self._queue: asyncio.Queue[Donation] = asyncio.Queue()
        self._processing = False
        self._process_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start processing notification queue."""
        if self._processing:
            return

        self._processing = True
        self._process_task = asyncio.create_task(self._process_queue())
        print("[NotificationService] Started")

    async def stop(self) -> None:
        """Stop processing notification queue."""
        self._processing = False

        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
            self._process_task = None

        print("[NotificationService] Stopped")

    async def notify(self, donation: Donation) -> None:
        """
        Show notification for donation immediately.
        Use queue_notification() for queued processing.
        """
        print(f"[NotificationService] Showing notification: {donation}")

        # Select media based on amount
        media = self._media_player.select_media(donation.amount)

        if media is None:
            print("[NotificationService] Warning: No media available")
            return

        # Show on web host
        duration = self._config.get_default_duration()
        await self._web_host.show_media(
            image_path=media.image_path,
            audio_path=media.audio_path,
            duration_ms=duration,
        )

    async def queue_notification(self, donation: Donation) -> None:
        """Add donation to notification queue."""
        await self._queue.put(donation)
        print(f"[NotificationService] Queued: {donation} (queue size: {self._queue.qsize()})")

    async def _process_queue(self) -> None:
        """Process notifications from queue one by one."""
        while self._processing:
            try:
                # Wait for donation with timeout to check _processing flag
                try:
                    donation = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # Show notification
                await self.notify(donation)

                # Wait for notification to finish (duration + buffer)
                duration = self._config.get_default_duration()
                await asyncio.sleep(duration / 1000 + 0.5)

                self._queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[NotificationService] Error processing queue: {e}")

    async def test_donation(self, amount: int = 10000) -> None:
        """
        Send test donation.
        Amount in kopecks (default 100 UAH = 10000 kopecks).
        """
        donation = Donation(
            amount=amount,
            currency="UAH",
            comment="Test donation",
            donor_name="Test User",
        )
        await self.notify(donation)

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()
