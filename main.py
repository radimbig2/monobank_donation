import asyncio
import sys
from pathlib import Path

from src.config import Config
from src.web_host import WebHost
from src.media_player import MediaPlayer
from src.notification import NotificationService
from src.monobank import MonobankClient
from src.poller import DonationPoller

PROJECT_ROOT = Path(__file__).parent.resolve()


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
            balance_uah = jar.balance / 100
            goal_str = f" / {jar.goal / 100:.2f}" if jar.goal else ""
            print(f"  {i}. {jar.title}")
            print(f"     Balance: {balance_uah:.2f}{goal_str} UAH")
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
    notification_service = NotificationService(web_host, media_player, config)

    # Connect notification service to web host for test button
    web_host.set_notification_service(notification_service)

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
    print("Add this URL as Browser Source in OBS")
    print("Press Ctrl+C to stop...\n")

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
