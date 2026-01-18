#!/usr/bin/env python3
"""Test notification service with YouTube player integration."""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.notification import NotificationService, Donation
from src.web_host import WebHost
from src.media_player import MediaPlayer
from src.youtube_player import YouTubePlayer

async def main():
    print("=" * 70)
    print("TEST: Notification Service + YouTube Player")
    print("=" * 70)

    config = Config(str(Path(__file__).parent / "config.yaml"))
    web_host = WebHost(config)
    media_player = MediaPlayer(config)
    notification_service = NotificationService(web_host, media_player, config)

    # Create YouTube player
    youtube_player = YouTubePlayer(queue_file=str(Path(__file__).parent / "youtube_queue.json"))

    # Set YouTube player in notification service
    notification_service.set_youtube_player(youtube_player)

    print(f"\n1. Created NotificationService")
    print(f"2. Created YouTubePlayer")
    print(f"3. Called set_youtube_player()")
    print(f"\nNotification Service has YouTube player: {notification_service._youtube_player is not None}")
    print(f"YouTube player object: {notification_service._youtube_player}")

    # Create a test donation with YouTube URL
    test_donation = Donation(
        amount=2000,  # 20 UAH
        comment="https://www.youtube.com/watch?v=pvgfto0hNsg test",
        donor_name="Test User"
    )

    print(f"\nCreated test donation:")
    print(f"  Comment: {test_donation.comment}")
    print(f"  Amount: {test_donation.amount_uah} UAH")

    print(f"\nCalling notify()...")
    await notification_service.notify(test_donation)

    print(f"\nDone!")
    print("=" * 70)

    youtube_player.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[Error] {e}")
        import traceback
        traceback.print_exc()
