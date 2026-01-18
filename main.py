#!/usr/bin/env python3
"""
Main application - runs both CLI console and GUI simultaneously.
"""

import asyncio
import sys
import threading
from pathlib import Path
from typing import Optional

try:
    from PyQt5.QtWidgets import QApplication
    HAS_PYQT5 = True
except ImportError:
    HAS_PYQT5 = False
    print("[Warning] PyQt5 not installed, running in console mode only")
    print("To enable GUI, run: pip install PyQt5")
    print()

from src.config import Config
from src.web_host import WebHost
from src.media_player import MediaPlayer
from src.notification import NotificationService
from src.monobank import MonobankClient
from src.poller import DonationPoller
from src.donations_feed import DonationsFeed
from src.youtube_player import YouTubePlayer
from src.youtube_player.queue_manager import QueueManager

if HAS_PYQT5:
    from src.youtube_player.gui import PlayerWindow

PROJECT_ROOT = Path(__file__).parent.resolve()

# Shared QueueManager instance for both async and GUI apps
SHARED_QUEUE_MANAGER: Optional[QueueManager] = None


def has_token(config: Config) -> bool:
    """Check if monobank token is configured."""
    token = config.get_monobank_token()
    return token and token != "YOUR_MONOBANK_TOKEN"


def has_jar_id(config: Config) -> bool:
    """Check if jar_id is configured."""
    jar_id = config.get_jar_id()
    return jar_id and jar_id != "YOUR_JAR_ID"


async def select_jar_interactive(config: Config) -> bool:
    """
    Interactive jar selection.
    Returns True if jar was selected, False if cancelled.
    """
    print("\n" + "=" * 50)
    print("JAR SELECTION")
    print("=" * 50)
    print("\nNo jar_id configured. Fetching your jars from Monobank...\n")

    try:
        monobank_client = MonobankClient(config)
        jars = await monobank_client.get_jars()

        if not jars:
            print("[Error] No jars found on your account!")
            print("Create a jar (банка) in Monobank app first.")
            return False

        print("Available jars:\n")
        for i, jar in enumerate(jars, 1):
            goal_str = f" / {jar.goal_uah:.2f}" if jar.goal_uah else ""
            print(f"  {i}. {jar.title}")
            print(f"     Balance: {jar.balance_uah:.2f}{goal_str} UAH")
            print(f"     ID: {jar.id}")
            if jar.description:
                print(f"     Description: {jar.description}")
            print()

        # Get user choice
        while True:
            try:
                choice = input(f"Select jar (1-{len(jars)}) or 'q' to quit: ").strip()

                if choice.lower() == 'q':
                    print("Cancelled.")
                    return False

                choice_num = int(choice)
                if 1 <= choice_num <= len(jars):
                    selected_jar = jars[choice_num - 1]
                    break
                else:
                    print(f"Please enter a number between 1 and {len(jars)}")
            except ValueError:
                print("Please enter a valid number")

        # Save to config
        print(f"\nSelected: {selected_jar.title}")
        print(f"Saving jar_id to config.yaml...")

        config.set_jar_id(selected_jar.id)

        print("Done!\n")
        return True

    except Exception as e:
        print(f"[Error] Failed to fetch jars: {e}")
        print("Check your token in config.yaml")
        return False


def start_input_listener(notification_service: "NotificationService") -> None:
    """
    Start listening for /test command in a separate thread.
    Formats:
      /test name                  -> name, text="тест", amount=100 UAH
      /test name text             -> name, text, amount=100 UAH
      /test name text amount      -> name, text, amount UAH
    Examples:
      /test Alice
      /test Bob "YouTube link"
      /test Charlie "https://youtu.be/xyz" 50
    """
    loop = asyncio.get_event_loop()

    def listen() -> None:
        print("[Input] Ready for test donations")
        print("[Input] /test name                    (name, text='test', 100 UAH)")
        print("[Input] /test name text               (name, text, 100 UAH)")
        print("[Input] /test name text amount        (name, text, amount UAH)")
        print("[Input] Example: /test Alice \"YouTube link\" 50")
        while True:
            try:
                user_input = input().strip()

                if not user_input:
                    continue

                if user_input.startswith("/test"):
                    # Parse /test command with flexible arguments
                    parts = user_input.split(maxsplit=1)
                    if len(parts) < 2:
                        print("[Input] Error: /test requires at least a name")
                        continue

                    # Remove /test and get remaining arguments
                    remaining = parts[1].strip()

                    # Split by spaces, but respect quoted strings
                    import shlex
                    try:
                        args = shlex.split(remaining)
                    except ValueError:
                        print("[Input] Error: invalid quotes in command")
                        continue

                    # Parse arguments with defaults
                    if len(args) < 1:
                        print("[Input] Error: /test requires at least a name")
                        continue

                    donor_name = args[0]
                    text = args[1] if len(args) > 1 else "test"
                    amount_uah = 100  # Default 100 UAH

                    # Try to parse amount if present
                    if len(args) > 2:
                        try:
                            amount_uah = float(args[2])
                        except ValueError:
                            print(f"[Input] Error: invalid amount '{args[2]}'. Expected number.")
                            continue

                    amount_kop = int(amount_uah * 100)

                    asyncio.run_coroutine_threadsafe(
                        notification_service.test_donation(
                            amount=amount_kop,
                            donor_name=donor_name,
                            comment=text
                        ),
                        loop
                    )
                    print(f"[Input] Test donation: {donor_name} - {amount_uah:.2f} UAH - {text}")
                else:
                    print("[Input] Unknown command. Use: /test name [text] [amount]")

            except Exception as e:
                print(f"[Input] Error: {e}")

    thread = threading.Thread(target=listen, daemon=True)
    thread.start()


async def main(queue_manager: Optional[QueueManager] = None):
    """Main async application."""
    # Initialize config
    config_path = PROJECT_ROOT / "config.yaml"

    if not config_path.exists():
        print(f"[Error] Config file not found: {config_path}")
        print("Copy config.example.yaml to config.yaml and configure it.")
        sys.exit(1)

    config = Config(str(config_path))

    # Check token
    if not has_token(config):
        print("[Error] Monobank token not configured!")
        print("Edit config.yaml and add your token.")
        print("Get token at: https://api.monobank.ua/")
        sys.exit(1)

    # Interactive jar selection if not configured
    if not has_jar_id(config):
        success = await select_jar_interactive(config)
        if not success:
            sys.exit(1)
        # Reload config after saving
        config.reload()

    # Initialize core components
    web_host = WebHost(config, project_root=PROJECT_ROOT)
    media_player = MediaPlayer(config, project_root=PROJECT_ROOT)
    donations_feed = DonationsFeed(config, max_donations=50)
    notification_service = NotificationService(web_host, media_player, config)

    # Connect components to each other
    web_host.set_notification_service(notification_service)
    web_host.set_donations_feed(donations_feed)
    notification_service.set_donations_feed(donations_feed)

    # Initialize monobank components
    monobank_client = MonobankClient(config)
    poller = DonationPoller(monobank_client, notification_service, config)

    # Initialize YouTube player with shared queue manager
    youtube_player = YouTubePlayer(queue_file=str(PROJECT_ROOT / "youtube_queue.json"), queue_manager=queue_manager)

    # Connect YouTube player to notification service for processing donation comments
    notification_service.set_youtube_player(youtube_player)

    print("[Main] Monobank integration enabled")
    print("[Main] YouTube player initialized")

    # Callback for new donations - add YouTube tracks to player
    async def on_donation(donation) -> None:
        """Handle new donation - check for YouTube link and minimum amount."""
        min_amount = config.get_min_donation_for_music()

        # Check if donation meets minimum amount for music
        if donation.amount_uah < min_amount:
            print(f"[Main] Donation {donation.amount_uah} UAH is below minimum {min_amount} UAH for music")
            return

        if donation.comment:
            await youtube_player.add_from_comment(donation.comment)

    poller.on_new_donation(on_donation)

    # Start services
    await web_host.start_async()
    await notification_service.start()
    await poller.start()
    await youtube_player.start()

    print(f"[Main] Polling for donations every {config.get_poll_interval()} seconds")
    print(f"\nServer running at {web_host.get_url()}")
    print("\nAvailable URLs:")
    print(f"  - Overlay (donations with media): {web_host.get_url()}/")
    print(f"  - Donations feed (list): {web_host.get_url()}/feed")
    print("\nAdd any of these URLs as Browser Source in OBS")
    print("Press Ctrl+C to stop...")

    # Start input listener for test donations
    start_input_listener(notification_service)

    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

    # Stop services
    await poller.stop()
    await notification_service.stop()
    await web_host.stop_async()
    await youtube_player.stop()
    youtube_player.cleanup()


def run_async_app(queue_manager: Optional[QueueManager] = None):
    """Run async application in a thread."""
    try:
        asyncio.run(main(queue_manager))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"[Error] {e}")
        import traceback
        traceback.print_exc()


def run_gui_app(queue_manager: Optional[QueueManager] = None):
    """Run GUI application."""
    if not HAS_PYQT5:
        print("[GUI] PyQt5 not available, skipping GUI")
        return

    config_path = PROJECT_ROOT / "config.yaml"
    if not config_path.exists():
        print("[Error] config.yaml not found!")
        return

    # Load config
    config = Config(str(config_path))

    # Create PyQt app
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Create YouTube player with shared queue manager
    player = YouTubePlayer(queue_file=str(PROJECT_ROOT / "youtube_queue.json"), queue_manager=queue_manager)

    # Create GUI window with config for volume persistence
    window = PlayerWindow(player, config=config)

    # Run GUI event loop
    try:
        app.exec_()
    except Exception as e:
        print(f"[GUI Error] {e}")
        import traceback
        traceback.print_exc()
    finally:
        player.cleanup()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🎵 Monobank Donation Tracker - Full Application")
    print("=" * 60)
    print("\nStarting:")
    print("  1. Web server (OBS overlay and feed)")
    print("  2. YouTube player (CLI control)")
    if HAS_PYQT5:
        print("  3. GUI interface (visual controls)")
    else:
        print("  3. (GUI disabled - install PyQt5 to enable)")
    print("\n" + "=" * 60 + "\n")

    try:
        # Create shared QueueManager instance
        queue_manager = QueueManager(queue_file=str(PROJECT_ROOT / "youtube_queue.json"))

        # Start async application in a separate thread
        async_thread = threading.Thread(target=run_async_app, args=(queue_manager,), daemon=True)
        async_thread.start()

        # Give async app time to initialize
        import time
        time.sleep(2)

        # Start GUI application in main thread if available
        if HAS_PYQT5:
            run_gui_app(queue_manager)
        else:
            # Just keep the async app running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass

    except KeyboardInterrupt:
        print("\n\nApplication closed")
    except Exception as e:
        print(f"\n[Error] {e}")
        import traceback
        traceback.print_exc()
