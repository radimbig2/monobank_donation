import asyncio
import sys
import threading
from pathlib import Path

from src.config import Config
from src.web_host import WebHost
from src.media_player import MediaPlayer
from src.notification import NotificationService
from src.monobank import MonobankClient
from src.poller import DonationPoller
from src.donations_feed import DonationsFeed

PROJECT_ROOT = Path(__file__).parent.resolve()


def has_token(config: Config) -> bool:
    """Check if monobank token is configured."""
    token = config.get_monobank_token()
    return token and token != "YOUR_MONOBANK_TOKEN"


def has_jar_id(config: Config) -> bool:
    """Check if jar_id is configured."""
    jar_id = config.get_jar_id()
    return jar_id and jar_id != "YOUR_JAR_ID"


def start_input_listener(notification_service: "NotificationService") -> None:
    """
    Start listening for Enter key in a separate thread.
    Sends a test donation when Enter is pressed.
    """
    loop = asyncio.get_event_loop()

    def listen() -> None:
        print("[Input] Ready for test donations - press Enter to send")
        while True:
            try:
                input()  # Block until Enter is pressed
                asyncio.run_coroutine_threadsafe(
                    notification_service.test_donation(),
                    loop
                )
                print("[Input] Test donation sent")
            except Exception as e:
                print(f"[Input] Error: {e}")

    thread = threading.Thread(target=listen, daemon=True)
    thread.start()


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


async def main():
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

    print("[Main] Monobank integration enabled")

    # Start services
    await web_host.start_async()
    await notification_service.start()
    await poller.start()

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


if __name__ == "__main__":
    asyncio.run(main())
