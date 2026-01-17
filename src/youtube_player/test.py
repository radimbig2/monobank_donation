#!/usr/bin/env python3
"""Test YouTube player module."""

import asyncio
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.youtube_player import (
    YouTubePlayer,
    YouTubeURLParser,
    QueueManager,
    QueueItem,
)


async def test_url_parser():
    """Test YouTube URL parser."""
    print("\n" + "=" * 60)
    print("Testing URLParser")
    print("=" * 60)

    parser = YouTubeURLParser()

    test_cases = [
        "Check this out: https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "Cool video youtu.be/dQw4w9WgXcQ",
        "No video here",
    ]

    for comment in test_cases:
        url = parser.extract_url(comment)
        print(f"Comment: {comment}")
        print(f"Extracted: {url}")
        if url:
            video_id = parser.extract_video_id(url)
            print(f"Video ID: {video_id}")
        print()


async def test_queue_manager():
    """Test queue manager."""
    print("\n" + "=" * 60)
    print("Testing QueueManager")
    print("=" * 60)

    qm = QueueManager("test_queue.json")
    qm.clear()

    # Add items
    item1 = QueueItem(
        url="https://youtube.com/watch?v=test1",
        title="Test Video 1",
        duration_sec=180,
    )
    item2 = QueueItem(
        url="https://youtube.com/watch?v=test2",
        title="Test Video 2",
        duration_sec=240,
    )

    qm.add(item1)
    qm.add(item2)

    print(f"Queue size: {qm.size()}")
    print(f"Queue items:")
    for item in qm.get_all():
        print(f"  - {item.title} ({item.duration_sec}s)")

    # Get next
    next_item = qm.get_next()
    print(f"\nNext item: {next_item.title}")

    # Mark as downloaded
    qm.mark_downloaded(0, "/path/to/file.mp3")
    print(f"Downloaded items: {qm.get_downloaded_count()}")

    # Remove
    qm.remove(0)
    print(f"After removal, queue size: {qm.size()}")

    qm.clear()
    print("Queue cleared")


async def test_player():
    """Test YouTube player."""
    print("\n" + "=" * 60)
    print("Testing YouTubePlayer")
    print("=" * 60)

    player = YouTubePlayer("test_player_queue.json")
    player.queue.clear()

    # Test adding from comment
    comments = [
        "Love this song! https://www.youtube.com/watch?v=jNQXAC9IVRw",
        "No video here",
        "Another one youtu.be/jNQXAC9IVRw",
    ]

    for comment in comments:
        print(f"\nComment: {comment}")
        result = await player.add_from_comment(comment)
        print(f"Added to queue: {result}")

    print(f"\nFinal queue size: {player.queue.size()}")

    player.queue.clear()


async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("YouTube Player Module Tests")
    print("=" * 60)

    await test_url_parser()
    await test_queue_manager()
    await test_player()

    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTests cancelled")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
