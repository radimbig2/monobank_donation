#!/usr/bin/env python3
"""Test adding track from donation comment."""
# -*- coding: utf-8 -*-

import sys
import io
import asyncio
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from src.youtube_player import YouTubePlayer

async def main():
    """Test adding track from comment."""
    print("=" * 70)
    print("TEST: Adding track from donation comment")
    print("=" * 70)

    player = YouTubePlayer(queue_file="youtube_queue_test.json")

    # Test comment from user
    test_comment = "https://music.youtube.com/watch?v=pvgfto0hNsg&si=jTXigAvJ1bOcqj-G hello"

    print(f"\nTest comment: {test_comment}")
    print()

    # Clear queue for testing
    queue = player.queue
    queue.clear()
    print(f"Queue cleared, size: {queue.size()}")
    print()

    print("Adding track from comment...")
    result = await player.add_from_comment(test_comment)

    print()
    print(f"Result: {result}")
    print()

    # Check queue
    items = queue.get_all()
    print(f"Queue size: {len(items)}")
    if items:
        for i, item in enumerate(items):
            print(f"  [{i}] {item.title}")
            print(f"      URL: {item.url}")
            print(f"      Duration: {item.duration_sec}s")
            print(f"      Downloaded: {item.downloaded}")
    else:
        print("  Queue is empty!")

    print()
    print("=" * 70)

    # Cleanup
    player.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[Error] {e}")
        import traceback
        traceback.print_exc()
