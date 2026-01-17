import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.config import Config
from src.web_host import WebHost

CONFIG_PATH = PROJECT_ROOT / "config.yaml"


async def test_server_start_stop():
    """Test that server starts and stops correctly."""
    config = Config(str(CONFIG_PATH))
    web_host = WebHost(config)

    assert not web_host.is_running()

    await web_host.start_async()
    assert web_host.is_running()
    assert web_host.get_url() == f"http://{config.get_host()}:{config.get_port()}"

    await web_host.stop_async()
    assert not web_host.is_running()

    print("[PASS] test_server_start_stop")


async def test_show_media():
    """Test showing media (requires manual browser check)."""
    config = Config(str(CONFIG_PATH))
    web_host = WebHost(config)

    await web_host.start_async()

    print(f"\n[INFO] Server running at {web_host.get_url()}")
    print("[INFO] Open this URL in browser and watch for media...")
    print("[INFO] Waiting 3 seconds before showing media...")

    await asyncio.sleep(3)

    # Show test media
    print("[INFO] Showing test image with audio...")
    await web_host.show_media(
        image_path="video/bebra.gif",
        audio_path="audio/donat_gitara.mp3",
        duration_ms=5000
    )

    print("[INFO] Waiting 6 seconds...")
    await asyncio.sleep(6)

    print("[INFO] Showing another image...")
    await web_host.show_image("video/200.gif", duration_ms=3000)

    await asyncio.sleep(4)

    await web_host.stop_async()
    print("[PASS] test_show_media")


async def run_server_interactive():
    """Run server interactively for manual testing."""
    config = Config(str(CONFIG_PATH))
    web_host = WebHost(config)

    await web_host.start_async()
    print(f"\n[INFO] Server running at {web_host.get_url()}")
    print("[INFO] Press Ctrl+C to stop...\n")

    try:
        while True:
            cmd = input("Enter command (show/clear/quit): ").strip().lower()

            if cmd == "quit" or cmd == "q":
                break
            elif cmd == "show":
                await web_host.show_media(
                    image_path="video/bebra.gif",
                    audio_path="audio/donat_gitara.mp3",
                    duration_ms=5000
                )
                print("[INFO] Media sent!")
            elif cmd == "clear":
                await web_host.clear()
                print("[INFO] Cleared!")
            else:
                print("[INFO] Unknown command. Use: show, clear, quit")

    except KeyboardInterrupt:
        pass

    await web_host.stop_async()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(run_server_interactive())
    else:
        asyncio.run(test_server_start_stop())
        asyncio.run(test_show_media())
        print("\nAll WebHost tests passed!")
