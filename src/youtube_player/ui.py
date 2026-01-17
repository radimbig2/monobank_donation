import asyncio
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .youtube_player import YouTubePlayer


class PlayerUI:
    """Text-based UI for YouTube player."""

    COMMANDS = {
        "p": "Пауза / Включить",
        "n": "Следующий трек",
        "v+": "Громче (+10%)",
        "v-": "Тише (-10%)",
        "q": "Список в очереди",
        "c": "Текущий трек",
        "s": "Выход",
        "?": "Помощь"
    }

    def __init__(self, player: "YouTubePlayer"):
        self.player = player
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
                cmd = input("\n[Player] > ").strip().lower()

                if not cmd:
                    continue

                if cmd == "p":
                    self._toggle_pause()
                elif cmd == "n":
                    self._next_track()
                elif cmd == "v+":
                    self._volume_up()
                elif cmd == "v-":
                    self._volume_down()
                elif cmd == "q":
                    self._show_queue()
                elif cmd == "c":
                    self._show_current()
                elif cmd == "s":
                    self._running = False
                    print("[Player] Выход...")
                elif cmd == "?":
                    self._print_help()
                else:
                    print(f"[Player] Неизвестная команда: {cmd}")

            except EOFError:
                break
            except Exception as e:
                print(f"[Player] Ошибка: {e}")

    def _toggle_pause(self) -> None:
        """Toggle pause."""
        if self.player.is_playing():
            if self.player.player.is_paused():
                self.player.resume()
                print("[Player] ▶ Включить")
            else:
                self.player.pause()
                print("[Player] ⏸ Пауза")
        else:
            print("[Player] Ничего не играет")

    def _next_track(self) -> None:
        """Skip to next track."""
        self.player.next_track()
        print("[Player] ⏭ Следующий трек")

    def _volume_up(self) -> None:
        """Increase volume."""
        vol = self.player.player.get_volume()
        self.player.set_volume(vol + 0.1)

    def _volume_down(self) -> None:
        """Decrease volume."""
        vol = self.player.player.get_volume()
        self.player.set_volume(vol - 0.1)

    def _show_queue(self) -> None:
        """Display queue."""
        queue = self.player.get_queue()
        if not queue:
            print("[Player] Очередь пуста")
            return

        print("\n" + "=" * 60)
        print("📋 ОЧЕРЕДЬ")
        print("=" * 60)
        for i, item in enumerate(queue, 1):
            status = "✓" if item.downloaded else "⏳"
            mins = item.duration_sec // 60
            secs = item.duration_sec % 60
            print(f"{i}. {status} {item.title[:40]}")
            print(f"   ⏱ {mins}:{secs:02d} | {item.url}")

    def _show_current(self) -> None:
        """Display current track."""
        current = self.player.get_current_track()
        if not current:
            print("[Player] Очередь пуста")
            return

        status = "Играет" if self.player.is_playing() else "Стоп"
        if self.player.player.is_paused():
            status = "⏸ Пауза"
        elif self.player.is_playing():
            status = "▶ Играет"

        vol = int(self.player.player.get_volume() * 100)
        mins = current.duration_sec // 60
        secs = current.duration_sec % 60

        print("\n" + "=" * 60)
        print("🎵 ТЕКУЩИЙ ТРЕК")
        print("=" * 60)
        print(f"Статус: {status}")
        print(f"Название: {current.title}")
        print(f"Длительность: {mins}:{secs:02d}")
        print(f"Громкость: {vol}%")
        print(f"URL: {current.url}")

    def _print_help(self) -> None:
        """Print help message."""
        print("\n" + "=" * 60)
        print("📖 КОМАНДЫ")
        print("=" * 60)
        for cmd, desc in self.COMMANDS.items():
            print(f"  {cmd:5s} - {desc}")
        print("=" * 60)
