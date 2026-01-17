#!/usr/bin/env python3
"""
YouTube Player GUI Application
Standalone application for managing YouTube music queue and playback.
"""

import sys
import asyncio
from pathlib import Path

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QThread, pyqtSignal

from src.youtube_player import YouTubePlayer
from src.youtube_player.gui import PlayerWindow
from src.config import Config


class PlayerWorker(QThread):
    """Worker thread for async player operations."""

    def __init__(self, player: YouTubePlayer):
        super().__init__()
        self.player = player
        self.loop = None

    def run(self):
        """Run async event loop."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Start player
        self.loop.run_until_complete(self.player.start())

        # Run event loop
        try:
            self.loop.run_forever()
        except:
            pass

    def stop(self):
        """Stop the event loop."""
        if self.loop:
            # Schedule stop
            async def do_stop():
                await self.player.stop()

            asyncio.run_coroutine_threadsafe(do_stop(), self.loop)
            self.loop.call_soon_threadsafe(self.loop.stop)


def main():
    """Main entry point for GUI application."""

    # Check config
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("[Error] config.yaml not found!")
        print("Copy config.example.yaml to config.yaml first")
        sys.exit(1)

    # Load config
    config = Config(str(config_path))

    # Create PyQt app
    app = QApplication(sys.argv)

    # Create YouTube player
    player = YouTubePlayer(queue_file="youtube_queue.json")

    # Create GUI window with config
    window = PlayerWindow(player, config=config)

    # Create worker thread for async operations
    worker = PlayerWorker(player)
    worker.start()

    def on_close():
        """Handle application close."""
        worker.stop()
        worker.wait()
        player.cleanup()

    # Connect close signal
    app.aboutToQuit.connect(on_close)

    # Run application (window already shown in PlayerWindow.__init__)
    sys.exit(app.exec_())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nGUI closed")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
