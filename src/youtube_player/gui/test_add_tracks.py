#!/usr/bin/env python3
"""Helper script to add test tracks to youtube_queue.json for testing."""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.youtube_player import YouTubePlayer, QueueItem


def add_test_tracks():
    """Add test tracks to queue for manual testing."""
    print("\n" + "="*60)
    print("YouTube Player Test Track Helper")
    print("="*60)

    # Known YouTube video IDs for testing (short videos)
    test_videos = [
        {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "name": "Rick Astley - Never Gonna Give You Up",
        },
        {
            "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
            "name": "Me at the zoo (first YouTube video)",
        },
    ]

    print("\nAvailable test tracks:")
    for i, video in enumerate(test_videos, 1):
        print(f"{i}. {video['name']}")
        print(f"   {video['url']}")

    print("\nWhich tracks do you want to add? (enter numbers separated by spaces, e.g. '1 2')")
    choice = input("> ").strip()

    if not choice:
        print("Cancelled.")
        return

    try:
        selected_indices = [int(x) - 1 for x in choice.split()]
        selected_videos = [test_videos[i] for i in selected_indices if 0 <= i < len(test_videos)]
    except (ValueError, IndexError):
        print("Invalid input.")
        return

    if not selected_videos:
        print("No valid selections.")
        return

    # Create/load player
    player = YouTubePlayer(queue_file="youtube_queue.json")

    print(f"\nAdding {len(selected_videos)} track(s) to queue...")

    for video in selected_videos:
        # Add to queue
        print(f"Adding: {video['name']}")
        player.queue.add(
            QueueItem(
                url=video['url'],
                title="Loading...",
                duration_sec=0
            )
        )

    print(f"\nAdded {len(selected_videos)} track(s) to youtube_queue.json")
    print("\nNext steps:")
    print("1. Run: python player_gui.py")
    print("2. Wait for tracks to download and titles to update from YouTube")
    print("3. Run: python src/youtube_player/gui/test.py")
    print("\nThe tests will then verify:")
    print("  - Track titles are updated from YouTube")
    print("  - Titles are persisted in youtube_queue.json")
    print("  - next_track() removes the current track and switches to next")


if __name__ == "__main__":
    try:
        add_test_tracks()
    except KeyboardInterrupt:
        print("\n\nCancelled.")
    except Exception as e:
        print(f"\n[Error] {e}")
        import traceback
        traceback.print_exc()
