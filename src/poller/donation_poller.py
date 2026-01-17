import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Callable

from src.notification import Donation

if TYPE_CHECKING:
    from src.config import Config
    from src.monobank import MonobankClient
    from src.notification import NotificationService


class DonationPoller:
    def __init__(
        self,
        monobank_client: "MonobankClient",
        notification_service: "NotificationService",
        config: "Config",
    ):
        self._monobank = monobank_client
        self._notification = notification_service
        self._config = config

        self._running = False
        self._poll_task: asyncio.Task | None = None

        # Track seen transaction IDs to avoid duplicates
        self._seen_tx_ids: set[str] = set()

        # Callbacks for new donations
        self._callbacks: list[Callable[[Donation], None]] = []

        # Track last poll time
        self._last_poll: datetime | None = None

    async def start(self) -> None:
        """Start polling for new donations."""
        if self._running:
            return

        self._running = True

        # Initial load: get recent transactions to mark as seen
        await self._initial_load()

        # Start polling task
        self._poll_task = asyncio.create_task(self._poll_loop())
        print("[DonationPoller] Started")

    async def stop(self) -> None:
        """Stop polling."""
        self._running = False

        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None

        print("[DonationPoller] Stopped")

    def is_running(self) -> bool:
        return self._running

    def on_new_donation(self, callback: Callable[[Donation], None]) -> None:
        """Register callback for new donations."""
        self._callbacks.append(callback)

    async def _initial_load(self) -> None:
        """Load recent transactions and mark them as seen."""
        try:
            # Get transactions from last hour to avoid showing old donations
            from_time = datetime.now() - timedelta(hours=1)
            transactions = await self._monobank.get_jar_transactions(from_time=from_time)

            for tx in transactions:
                self._seen_tx_ids.add(tx.id)

            print(f"[DonationPoller] Initial load: marked {len(transactions)} transactions as seen")

        except Exception as e:
            print(f"[DonationPoller] Error during initial load: {e}")

    async def _poll_loop(self) -> None:
        """Main polling loop."""
        interval = self._config.get_poll_interval()

        while self._running:
            try:
                await self._poll_once()
            except Exception as e:
                print(f"[DonationPoller] Error during poll: {e}")

            # Wait for next poll
            await asyncio.sleep(interval)

    async def _poll_once(self) -> list[Donation]:
        """Check for new donations once."""
        # Get recent transactions
        from_time = self._last_poll or (datetime.now() - timedelta(hours=1))
        self._last_poll = datetime.now()

        try:
            transactions = await self._monobank.get_jar_transactions(from_time=from_time)
        except Exception as e:
            print(f"[DonationPoller] Error getting transactions: {e}")
            return []

        new_donations = []

        for tx in transactions:
            # Skip already seen transactions
            if tx.id in self._seen_tx_ids:
                continue

            # Mark as seen
            self._seen_tx_ids.add(tx.id)

            # Create donation object
            donation = Donation(
                amount=tx.amount,
                currency="UAH",
                comment=tx.comment or tx.description,
                timestamp=tx.time,
                donor_name=tx.donor_name,
            )

            new_donations.append(donation)
            print(f"[DonationPoller] New donation: {donation}")

            # Queue notification
            await self._notification.queue_notification(donation)

            # Call callbacks
            for callback in self._callbacks:
                try:
                    callback(donation)
                except Exception as e:
                    print(f"[DonationPoller] Callback error: {e}")

        if new_donations:
            print(f"[DonationPoller] Found {len(new_donations)} new donation(s)")

        return new_donations

    async def poll_once(self) -> list[Donation]:
        """Manual poll for testing."""
        return await self._poll_once()

    def get_seen_count(self) -> int:
        """Get number of seen transactions."""
        return len(self._seen_tx_ids)

    def clear_seen(self) -> None:
        """Clear seen transactions (for testing)."""
        self._seen_tx_ids.clear()
