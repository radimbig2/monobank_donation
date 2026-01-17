import asyncio
import sys
from pathlib import Path

from src.config import Config
from src.web_host import WebHost
from src.media_player import MediaPlayer
from src.notification import NotificationService

PROJECT_ROOT = Path(__file__).parent.resolve()


async def main():
    # Initialize all components
    config = Config(str(PROJECT_ROOT / "config.yaml"))
    web_host = WebHost(config, project_root=PROJECT_ROOT)
    media_player = MediaPlayer(config, project_root=PROJECT_ROOT)
    notification_service = NotificationService(web_host, media_player, config)

    # Connect notification service to web host for test button
    web_host.set_notification_service(notification_service)

    # Start services
    await web_host.start_async()
    await notification_service.start()

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
    await notification_service.stop()
    await web_host.stop_async()


if __name__ == "__main__":
    asyncio.run(main())
