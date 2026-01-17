import json
import weakref
from typing import TYPE_CHECKING

from aiohttp import web

if TYPE_CHECKING:
    from src.notification import Donation
    from src.config import Config


class DonationsFeed:
    """Manages donations list and broadcasts updates to connected clients."""

    def __init__(self, config: "Config", max_donations: int = 50):
        self._config = config
        self._max_donations = max_donations

        # List of donations (oldest first)
        self._donations: list["Donation"] = []

        # Connected WebSocket clients
        self._websockets: weakref.WeakSet = weakref.WeakSet()

    def add_donation(self, donation: "Donation") -> None:
        """Add donation to feed and broadcast to clients."""
        # Add to list
        self._donations.append(donation)

        # Keep only last N donations
        if len(self._donations) > self._max_donations:
            self._donations = self._donations[-self._max_donations:]

        print(f"[DonationsFeed] Added donation. Total: {len(self._donations)}")

    async def register_websocket(self, ws: web.WebSocketResponse) -> None:
        """Register a new WebSocket client."""
        self._websockets.add(ws)
        print(f"[DonationsFeed] WebSocket connected. Total: {len(self._websockets)}")

        # Send current donations
        await self._send_current_donations(ws)

    def unregister_websocket(self, ws: web.WebSocketResponse) -> None:
        """Unregister a WebSocket client."""
        self._websockets.discard(ws)
        print(f"[DonationsFeed] WebSocket disconnected. Total: {len(self._websockets)}")

    async def broadcast_new_donation(self, donation: "Donation") -> None:
        """Broadcast new donation to all connected clients."""
        message = self._donation_to_dict(donation)
        await self._broadcast({"type": "new_donation", "donation": message})

    async def _send_current_donations(self, ws: web.WebSocketResponse) -> None:
        """Send all current donations to a client."""
        donations_data = [self._donation_to_dict(d) for d in self._donations]
        message = json.dumps({
            "type": "init",
            "donations": donations_data
        })
        try:
            await ws.send_str(message)
        except Exception as e:
            print(f"[DonationsFeed] Error sending current donations: {e}")

    async def _broadcast(self, message: dict) -> None:
        """Broadcast message to all connected clients."""
        if not self._websockets:
            return

        data = json.dumps(message)
        tasks = []

        for ws in list(self._websockets):
            if not ws.closed:
                tasks.append(ws.send_str(data))

        if tasks:
            import asyncio
            await asyncio.gather(*tasks, return_exceptions=True)

    @staticmethod
    def _donation_to_dict(donation: "Donation") -> dict:
        """Convert donation object to dictionary for JSON serialization."""
        return {
            "donor_name": donation.donor_name or "Anonymous",
            "amount": donation.amount / 100,  # Convert to UAH
            "comment": donation.comment or "",
            "timestamp": int(donation.timestamp.timestamp()),
        }

    def get_donations(self) -> list["Donation"]:
        """Get current donations list."""
        return self._donations.copy()

    def clear(self) -> None:
        """Clear all donations."""
        self._donations.clear()
