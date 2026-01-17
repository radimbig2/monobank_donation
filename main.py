import asyncio
import sys

from src.config import Config
from src.web_host import WebHost


async def main():
    config = Config("config.yaml")
    web_host = WebHost(config)

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
