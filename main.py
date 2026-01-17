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


def is_monobank_configured(config: Config) -> bool:
    """Check if monobank credentials are configured."""
    return (
        config.get_monobank_token() != "YOUR_MONOBANK_TOKEN"
        and config.get_jar_id() != "YOUR_JAR_ID"
    )


async def main():
    # Initialize config
    config = Config(str(PROJECT_ROOT / "config.yaml"))

    # Initialize core components
    web_host = WebHost(config, project_root=PROJECT_ROOT)
    media_player = MediaPlayer(config, project_root=PROJECT_ROOT)
    notification_service = NotificationService(web_host, media_player, config)

    # Connect notification service to web host for test button
    web_host.set_notification_service(notification_service)

    # Initialize monobank components (optional)
    poller = None
    if is_monobank_configured(config):
        monobank_client = MonobankClient(config)
        poller = DonationPoller(monobank_client, notification_service, config)
        print("[Main] Monobank integration enabled")
    else:
        print("[Main] Monobank not configured - running in test mode only")
        print("[Main] Edit config.yaml to add your token and jar_id")

    # Start services
    await web_host.start_async()
    await notification_service.start()

    if poller:
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
    if poller:
        await poller.stop()
    await notification_service.stop()
    await web_host.stop_async()


if __name__ == "__main__":
    asyncio.run(main())
