import asyncio
import sys
from pathlib import Path

# Allow running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.config import Config
    from src.web_host import WebHost
    from src.media_player import MediaPlayer
    from src.notification import NotificationService
    from src.monobank import MonobankClient
    from src.poller.donation_poller import DonationPoller
else:
    from src.config import Config
    from src.web_host import WebHost
    from src.media_player import MediaPlayer
    from src.notification import NotificationService
    from src.monobank import MonobankClient
    from .donation_poller import DonationPoller

PROJECT_ROOT = Path(__file__).parent.parent.parent


def is_configured(config: Config) -> bool:
    """Check if monobank is configured."""
    return (
        config.get_monobank_token() != "YOUR_MONOBANK_TOKEN"
        and config.get_jar_id() != "YOUR_JAR_ID"
    )


async def test_poller_start_stop():
    """Test poller start/stop without real API."""
    config = Config(str(PROJECT_ROOT / "config.yaml"))

    if not is_configured(config):
        print("[SKIP] test_poller_start_stop - not configured")
        return

    web_host = WebHost(config, project_root=PROJECT_ROOT)
    media_player = MediaPlayer(config, project_root=PROJECT_ROOT)
    notification_service = NotificationService(web_host, media_player, config)
    monobank_client = MonobankClient(config)
    poller = DonationPoller(monobank_client, notification_service, config)

    await web_host.start_async()

    assert not poller.is_running()

    await poller.start()
    assert poller.is_running()
    print(f"[INFO] Seen transactions after initial load: {poller.get_seen_count()}")

    await asyncio.sleep(2)

    await poller.stop()
    assert not poller.is_running()

    await web_host.stop_async()

    print("[PASS] test_poller_start_stop")


async def test_poll_once():
    """Test single poll."""
    config = Config(str(PROJECT_ROOT / "config.yaml"))

    if not is_configured(config):
        print("[SKIP] test_poll_once - not configured")
        return

    web_host = WebHost(config, project_root=PROJECT_ROOT)
    media_player = MediaPlayer(config, project_root=PROJECT_ROOT)
    notification_service = NotificationService(web_host, media_player, config)
    monobank_client = MonobankClient(config)
    poller = DonationPoller(monobank_client, notification_service, config)

    # Manual poll without starting the loop
    donations = await poller.poll_once()
    print(f"[INFO] Poll returned {len(donations)} new donations")

    # Second poll should return 0 (same transactions seen)
    donations2 = await poller.poll_once()
    print(f"[INFO] Second poll returned {len(donations2)} new donations")

    print("[PASS] test_poll_once")


async def test_full_integration():
    """Test full integration with real API and web server."""
    config = Config(str(PROJECT_ROOT / "config.yaml"))

    if not is_configured(config):
        print("[SKIP] test_full_integration - not configured")
        return

    print("\n[INFO] Starting full integration test...")
    print("[INFO] Open browser at http://localhost:8080 to see donations")
    print("[INFO] Press Ctrl+C to stop\n")

    web_host = WebHost(config, project_root=PROJECT_ROOT)
    media_player = MediaPlayer(config, project_root=PROJECT_ROOT)
    notification_service = NotificationService(web_host, media_player, config)
    monobank_client = MonobankClient(config)
    poller = DonationPoller(monobank_client, notification_service, config)

    web_host.set_notification_service(notification_service)

    await web_host.start_async()
    await notification_service.start()
    await poller.start()

    print(f"[INFO] Server running at {web_host.get_url()}")
    print(f"[INFO] Polling every {config.get_poll_interval()} seconds")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] Stopping...")

    await poller.stop()
    await notification_service.stop()
    await web_host.stop_async()

    print("[PASS] test_full_integration")


if __name__ == "__main__":
    print("DonationPoller Tests")
    print("=" * 50 + "\n")

    asyncio.run(test_poll_once())
    asyncio.run(test_poller_start_stop())

    # Uncomment to run full integration test
    # asyncio.run(test_full_integration())

    print("\nAll DonationPoller tests completed!")
