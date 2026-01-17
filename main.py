import asyncio
import sys
from pathlib import Path

from src.config import Config
from src.web_host import WebHost

PROJECT_ROOT = Path(__file__).parent.resolve()


async def main():
    config = Config(str(PROJECT_ROOT / "config.yaml"))
    web_host = WebHost(config, project_root=PROJECT_ROOT)

    await web_host.start_async()
    print(f"\nServer running at {web_host.get_url()}")
    print("Add this URL as Browser Source in OBS")
    print("Press Ctrl+C to stop...\n")

    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

    await web_host.stop_async()


if __name__ == "__main__":
    asyncio.run(main())
