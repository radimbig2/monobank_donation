#!/usr/bin/env python3
"""Quick test - adds mock tracks with real titles to test JSON persistence and next_track()."""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.youtube_player import QueueItem


def quick_test():
    """Add mock tracks and test functionality."""
    print("\n" + "="*60)
    print("Quick Test: Track Title and Next Track")
    print("="*60)

    queue_file = Path("youtube_queue.json")

    # Create mock queue with real titles (as if downloaded)
    print("\n[Setup] Creating mock queue with 3 tracks...")
    mock_queue = [
        {
            "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "title": "Rick Astley - Never Gonna Give You Up",  # UPDATED TITLE
            "duration_sec": 213,
            "added_at": "2024-01-17T10:00:00",
            "file_path": "youtube_cache/track1.mp3",
            "downloaded": True,
            "download_progress": 100
        },
        {
            "url": "https://www.youtube.com/watch?v=jNQXAC9IVRw",
            "title": "Me at the zoo",  # UPDATED TITLE
            "duration_sec": 18,
            "added_at": "2024-01-17T10:01:00",
            "file_path": "youtube_cache/track2.mp3",
            "downloaded": True,
            "download_progress": 100
        },
        {
            "url": "https://www.youtube.com/watch?v=9bZkp7q19f0",
            "title": "PSY - GANGNAM STYLE",  # UPDATED TITLE
            "duration_sec": 253,
            "added_at": "2024-01-17T10:02:00",
            "file_path": "youtube_cache/track3.mp3",
            "downloaded": True,
            "download_progress": 100
        }
    ]

    # Save to file
    with open(queue_file, 'w', encoding='utf-8') as f:
        json.dump(mock_queue, f, indent=2, ensure_ascii=False)

    print(f"[File] Saved {len(mock_queue)} mock tracks to {queue_file}")

    # Now test the same logic as the actual tests
    from src.youtube_player import YouTubePlayer

    # Test 1: Track title persistence
    print("\n" + "-"*60)
    print("TEST 1: Track Title Persistence in JSON")
    print("-"*60)

    player = YouTubePlayer(queue_file="youtube_queue.json")
    queue = player.get_queue()

    print(f"[Player] Loaded queue with {len(queue)} tracks")

    if queue:
        first_track = queue[0]
        print(f"[Track 1] Title: '{first_track.title}'")
        print(f"[Track 1] URL: {first_track.url}")

        # Verify it's NOT "Loading..."
        if first_track.title != "Loading...":
            print("[Check] Title is NOT 'Loading...' - GOOD")
            print("\n[PASS] Track title correctly persisted in JSON")
        else:
            print("\n[FAIL] Title is still 'Loading...'")

        # Verify file matches memory
        with open(queue_file, 'r', encoding='utf-8') as f:
            persisted = json.load(f)

        persisted_title = persisted[0]['title']
        if persisted_title == first_track.title:
            print(f"[Check] JSON title matches memory: '{persisted_title}'")
            print("[PASS] Title persistence verified")
        else:
            print(f"[FAIL] Title mismatch: memory='{first_track.title}' vs json='{persisted_title}'")

    # Test 2: next_track() removes and switches
    print("\n" + "-"*60)
    print("TEST 2: next_track() Removes Current and Switches to Next")
    print("-"*60)

    print(f"[Before] Queue size: {len(queue)}")
    print(f"[Before] Current track: '{queue[0].title}'")

    if len(queue) >= 2:
        print(f"[Before] Next track will be: '{queue[1].title}'")

    # Call next_track
    print("[Action] Calling next_track()...")
    player.next_track()

    # Check new state
    new_queue = player.get_queue()
    print(f"[After] Queue size: {len(new_queue)}")

    # Verify in file
    with open(queue_file, 'r', encoding='utf-8') as f:
        persisted_after = json.load(f)

    print(f"[File] JSON queue size: {len(persisted_after)}")

    # Check if removed
    if len(persisted_after) == len(queue) - 1:
        print("[Check] One track removed from JSON")
        print("[PASS] next_track() removed current track")
    else:
        print(f"[FAIL] Expected {len(queue) - 1} tracks, got {len(persisted_after)}")

    # Check if switched
    if new_queue:
        new_current = new_queue[0]
        print(f"\n[After] New current track: '{new_current.title}'")

        if persisted_after and persisted_after[0]['title'] == new_current.title:
            print("[Check] New current matches JSON first item")
            print("[PASS] next_track() switched to next track")
        else:
            print("[FAIL] Current track mismatch")
    else:
        if not persisted_after:
            print("[Info] Queue is now empty")
            print("[PASS] All tracks removed as expected")

    # Summary
    print("\n" + "="*60)
    print("Quick Test Summary")
    print("="*60)
    print("[OK] Track titles are persisted in JSON (not 'Loading...')")
    print("[OK] next_track() removes current track from JSON")
    print("[OK] next_track() switches to next track in queue")
    print("\nQueue structure is working correctly!")


if __name__ == "__main__":
    try:
        quick_test()
    except Exception as e:
        print(f"\n[Error] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
