import asyncio
import sys
from pathlib import Path

# Allow running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.config import Config
    from src.web_host import WebHost
    from src.media_player import MediaPlayer
    from src.notification.notification_service import NotificationService, Donation
else:
    from src.config import Config
    from src.web_host import WebHost
    from src.media_player import MediaPlayer
    from .notification_service import NotificationService, Donation

PROJECT_ROOT = Path(__file__).parent.parent.parent


def test_donation_dataclass():
    """Test Donation dataclass."""
    donation = Donation(
        amount=15000,
        currency="UAH",
        comment="Hello!",
        donor_name="John",
    )

    assert donation.amount == 15000
    assert donation.amount_uah == 150.0
    assert "John" in str(donation)
    assert "150" in str(donation)

    print(f"[INFO] Donation: {donation}")
    print("[PASS] test_donation_dataclass")


async def test_notification_service():
    """Test NotificationService with real WebHost."""
    config = Config(str(PROJECT_ROOT / "config.yaml"))
    web_host = WebHost(config, project_root=PROJECT_ROOT)
    media_player = MediaPlayer(config, project_root=PROJECT_ROOT)
    notification_service = NotificationService(web_host, media_player, config)

    await web_host.start_async()

    print(f"\n[INFO] Server running at {web_host.get_url()}")
    print("[INFO] Open browser to see notifications...")
    print("[INFO] Waiting 3 seconds...")

    await asyncio.sleep(3)

    # Test different donation amounts
    test_donations = [
        Donation(amount=2000, donor_name="Small Donor", comment="Small donation"),
        Donation(amount=7500, donor_name="Medium Donor", comment="Medium donation"),
        Donation(amount=25000, donor_name="Big Donor", comment="Big donation!"),
    ]

    for donation in test_donations:
        print(f"\n[INFO] Sending: {donation}")
        await notification_service.notify(donation)
        await asyncio.sleep(6)  # Wait for notification to finish

    await web_host.stop_async()
    print("[PASS] test_notification_service")


async def test_queue():
    """Test notification queue."""
    config = Config(str(PROJECT_ROOT / "config.yaml"))
    web_host = WebHost(config, project_root=PROJECT_ROOT)
    media_player = MediaPlayer(config, project_root=PROJECT_ROOT)
    notification_service = NotificationService(web_host, media_player, config)

    await web_host.start_async()
    await notification_service.start()

    print(f"\n[INFO] Server running at {web_host.get_url()}")
    print("[INFO] Testing queue - adding 3 donations at once...")

    await asyncio.sleep(2)

    # Queue multiple donations
    await notification_service.queue_notification(
        Donation(amount=1000, donor_name="User1")
    )
    await notification_service.queue_notification(
        Donation(amount=5000, donor_name="User2")
    )
    await notification_service.queue_notification(
        Donation(amount=10000, donor_name="User3")
    )

    print(f"[INFO] Queue size: {notification_service.get_queue_size()}")

    # Wait for all to process
    await asyncio.sleep(20)

    await notification_service.stop()
    await web_host.stop_async()
    print("[PASS] test_queue")


async def test_test_donation():
    """Test the test_donation helper."""
    config = Config(str(PROJECT_ROOT / "config.yaml"))
    web_host = WebHost(config, project_root=PROJECT_ROOT)
    media_player = MediaPlayer(config, project_root=PROJECT_ROOT)
    notification_service = NotificationService(web_host, media_player, config)

    await web_host.start_async()

    print(f"\n[INFO] Server running at {web_host.get_url()}")
    print("[INFO] Sending test donation...")

    await asyncio.sleep(2)
    await notification_service.test_donation(15000)  # 150 UAH
    await asyncio.sleep(6)

    await web_host.stop_async()
    print("[PASS] test_test_donation")


if __name__ == "__main__":
    test_donation_dataclass()

    print("\n" + "=" * 50)
    print("Running integration test (requires browser)...")
    print("=" * 50)

    asyncio.run(test_test_donation())

    print("\nAll NotificationService tests passed!")
