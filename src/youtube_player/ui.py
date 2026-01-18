import asyncio
import threading
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .youtube_player import YouTubePlayer
    from src.notification import NotificationService


class PlayerUI:
    """Text-based UI for YouTube player."""

    COMMANDS = {
        "p": "Pause / Play",
        "n": "Next track",
        "v+": "Increase volume +10% or v+ 15 (current + 15%)",
        "v-": "Decrease volume -10% or v- 2 (current - 2%)",
        "v": "Set volume to exact % (v 20 = set to 20%)",
        "q": "Queue list",
        "c": "Current track",
        "s": "Exit",
        "/test": "Send test donation with YouTube track",
        "?": "Help"
    }

    def __init__(self, player: "YouTubePlayer", notification_service: Optional["NotificationService"] = None, event_loop=None):
        self.player = player
        self.notification_service = notification_service
        self.event_loop = event_loop  # Main event loop for async operations
        self._running = False

    def start(self) -> None:
        """Start UI loop in separate thread."""
        self._running = True
        thread = threading.Thread(target=self._ui_loop, daemon=True)
        thread.start()
        print("\n" + "=" * 60)
        print("YouTube Player Interface")
        print("=" * 60)
        self._print_help()

    def stop(self) -> None:
        """Stop UI loop."""
        self._running = False

    def _ui_loop(self) -> None:
        """Main UI loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while self._running:
            try:
                cmd = input("\n[Player] > ").strip()

                if not cmd:
                    continue

                # Check for /test command (case-sensitive)
                if cmd.startswith("/test"):
                    self._handle_test_command(cmd, loop)
                else:
                    # Regular commands (case-insensitive)
                    cmd_lower = cmd.lower().strip()

                    # Check for volume commands
                    if cmd_lower.startswith("v+"):
                        # v+ 15 = increase current volume by 15%
                        parts = cmd_lower.split()
                        if len(parts) > 1:
                            try:
                                delta = int(parts[1])
                                self._volume_adjust(delta)
                            except ValueError:
                                print("[Player] Error: v+ requires a number. Usage: v+ 15")
                        else:
                            self._volume_up()  # v+ alone = +10%
                    elif cmd_lower.startswith("v-"):
                        # v- 2 = decrease current volume by 2%
                        parts = cmd_lower.split()
                        if len(parts) > 1:
                            try:
                                delta = int(parts[1])
                                self._volume_adjust(-delta)
                            except ValueError:
                                print("[Player] Error: v- requires a number. Usage: v- 2")
                        else:
                            self._volume_down()  # v- alone = -10%
                    elif cmd_lower.startswith("v "):
                        # v 20 = set volume to exactly 20%
                        parts = cmd_lower.split()
                        if len(parts) > 1:
                            try:
                                volume = int(parts[1])
                                self._set_volume(volume)
                            except ValueError:
                                print("[Player] Error: v requires a number (0-100). Usage: v 20")
                        else:
                            print("[Player] Error: v requires a number. Usage: v 20")
                    elif cmd_lower == "p":
                        self._toggle_pause()
                    elif cmd_lower == "n":
                        self._next_track()
                    elif cmd_lower == "q":
                        self._show_queue()
                    elif cmd_lower == "c":
                        self._show_current()
                    elif cmd_lower == "s":
                        self._running = False
                        print("[Player] Exiting...")
                    elif cmd_lower == "?":
                        self._print_help()
                    else:
                        print(f"[Player] Unknown command: {cmd_lower}")

            except EOFError:
                break
            except Exception as e:
                print(f"[Player] Error: {e}")

    def _toggle_pause(self) -> None:
        """Toggle pause/play - same logic as GUI."""
        # Reload queue from disk to get latest changes (in case track was added by /test)
        self.player.queue.load()

        current = self.player.get_current_track()

        print(f"[Player] Toggle called")
        print(f"[Player] Current track: {current.title if current else 'None'}")

        if not current:
            print(f"[Player] Queue is empty")
            return

        print(f"[Player] Track downloaded: {current.downloaded}, file_path: {current.file_path}")

        if not current.downloaded:
            print(f"[Player] Track is still downloading...")
            return

        # Toggle pause/play using same method as GUI
        is_playing_before = self.player.player.is_playing()
        print(f"[Player] Is playing before toggle: {is_playing_before}")

        self.player.pause()  # Same method as GUI - handles play/pause/resume

        is_paused_after = self.player.player.is_paused()
        is_playing_after = self.player.player.is_playing()
        print(f"[Player] Is paused after: {is_paused_after}, is_playing after: {is_playing_after}")

        status = "Paused" if is_paused_after else "Playing"
        print(f"[Player] Status: {status}")

    def _next_track(self) -> None:
        """Skip to next track."""
        self.player.next_track()
        print("[Player] ⏭ Next track")

    def _volume_up(self) -> None:
        """Increase volume."""
        vol = self.player.player.get_volume()
        new_vol = min(1.0, vol + 0.1)
        self.player.set_volume(new_vol)
        print(f"[Player] Volume: {int(new_vol * 100)}%")

    def _volume_down(self) -> None:
        """Decrease volume."""
        vol = self.player.player.get_volume()
        new_vol = max(0.0, vol - 0.1)
        self.player.set_volume(new_vol)
        print(f"[Player] Volume: {int(new_vol * 100)}%")

    def _set_volume(self, percentage: int) -> None:
        """Set volume to specific percentage (0-100)."""
        percentage = max(0, min(100, percentage))  # Clamp 0-100
        volume = percentage / 100.0
        self.player.set_volume(volume)
        print(f"[Player] Volume: {percentage}%")

    def _volume_adjust(self, delta: int) -> None:
        """Adjust volume by delta percentage points."""
        current_vol = self.player.player.get_volume()
        current_percentage = int(current_vol * 100)
        new_percentage = current_percentage + delta
        new_percentage = max(0, min(100, new_percentage))  # Clamp 0-100

        volume = new_percentage / 100.0
        self.player.set_volume(volume)
        print(f"[Player] Volume: {current_percentage}% → {new_percentage}%")

    def _show_queue(self) -> None:
        """Display queue."""
        # Reload queue from disk to show latest changes
        self.player.queue.load()
        queue = self.player.get_queue()
        if not queue:
            print("[Player] Queue is empty")
            return

        print("\n" + "=" * 60)
        print("📋 QUEUE")
        print("=" * 60)
        for i, item in enumerate(queue, 1):
            status = "✓" if item.downloaded else "⏳"
            mins = item.duration_sec // 60
            secs = item.duration_sec % 60
            print(f"{i}. {status} {item.title[:40]}")
            print(f"   ⏱ {mins}:{secs:02d} | {item.url}")

    def _show_current(self) -> None:
        """Display current track."""
        # Reload queue from disk to show latest changes
        self.player.queue.load()
        current = self.player.get_current_track()
        if not current:
            print("[Player] Queue is empty")
            return

        status = "Playing" if self.player.is_playing() else "Stopped"
        if self.player.player.is_paused():
            status = "⏸ Paused"
        elif self.player.is_playing():
            status = "▶ Playing"

        vol = int(self.player.player.get_volume() * 100)
        mins = current.duration_sec // 60
        secs = current.duration_sec % 60

        print("\n" + "=" * 60)
        print("🎵 CURRENT TRACK")
        print("=" * 60)
        print(f"Status: {status}")
        print(f"Title: {current.title}")
        print(f"Duration: {mins}:{secs:02d}")
        print(f"Volume: {vol}%")
        print(f"URL: {current.url}")

    def _handle_test_command(self, cmd: str, loop) -> None:
        """Handle /test command for test donations."""
        if not self.notification_service:
            print("[Player] Notification service not available")
            return

        if not self.event_loop:
            print("[Player] Event loop not available")
            return

        # Parse /test command
        parts = cmd.split(maxsplit=1)
        if len(parts) < 2:
            print("[Player] Error: /test requires at least a name")
            print("[Player] Usage: /test name [text] [amount]")
            return

        remaining = parts[1].strip()

        # Split by spaces, but respect quoted strings
        import shlex
        try:
            args = shlex.split(remaining)
        except ValueError:
            print("[Player] Error: invalid quotes in command")
            return

        if len(args) < 1:
            print("[Player] Error: /test requires at least a name")
            return

        donor_name = args[0]
        text = args[1] if len(args) > 1 else "test"
        amount_uah = 100  # Default 100 UAH

        # Try to parse amount if present
        if len(args) > 2:
            try:
                amount_uah = float(args[2])
            except ValueError:
                print(f"[Player] Error: invalid amount '{args[2]}'. Expected number.")
                return

        amount_kop = int(amount_uah * 100)

        # Send test donation via notification service using main event loop
        asyncio.run_coroutine_threadsafe(
            self.notification_service.test_donation(
                amount=amount_kop,
                donor_name=donor_name,
                comment=text
            ),
            self.event_loop  # Use main event loop, not UI thread loop
        )
        print(f"[Player] Test donation: {donor_name} - {amount_uah:.2f} UAH - {text}")

    def _print_help(self) -> None:
        """Print help message."""
        print("\n" + "=" * 60)
        print("📖 COMMANDS")
        print("=" * 60)
        for cmd, desc in self.COMMANDS.items():
            print(f"  {cmd:5s} - {desc}")
        print("=" * 60)
