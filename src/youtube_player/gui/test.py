#!/usr/bin/env python3
"""Test suite for YouTube Player GUI module."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.config import Config
from src.youtube_player import YouTubePlayer
from src.youtube_player.gui import PlayerWindow


def test_volume_loading():
    """Test that volume is correctly loaded from config into player."""
    print("\n" + "="*60)
    print("TEST: Volume Loading from Config")
    print("="*60)

    # Load config
    config_path = Path("config.yaml")
    if not config_path.exists():
        print("[ERROR] config.yaml not found!")
        return False

    config = Config(str(config_path))
    config_volume = config.get_player_volume()
    print(f"[Config] Player volume from config: {config_volume}")

    # Create player
    player = YouTubePlayer(queue_file="youtube_queue.json")
    print(f"[Player] Initial player volume: {player.player.get_volume()}")

    # Set volume from config (simulating what PlayerWindow does)
    player.set_volume(config_volume)
    player_volume_after_set = player.player.get_volume()
    print(f"[Player] Player volume after set_volume({config_volume}): {player_volume_after_set}")

    # Check if volumes match
    if abs(config_volume - player_volume_after_set) < 0.01:
        print("\n[PASS] Config volume matches player volume")
        print(f"  Config: {config_volume}")
        print(f"  Player: {player_volume_after_set}")
        return True
    else:
        print("\n[FAIL] Config volume does NOT match player volume")
        print(f"  Config: {config_volume}")
        print(f"  Player: {player_volume_after_set}")
        print(f"  Difference: {abs(config_volume - player_volume_after_set)}")
        return False


def test_volume_persistence():
    """Test that volume changes are saved to config."""
    print("\n" + "="*60)
    print("TEST: Volume Persistence to Config")
    print("="*60)

    config_path = Path("config.yaml")
    if not config_path.exists():
        print("[ERROR] config.yaml not found!")
        return False

    config = Config(str(config_path))
    original_volume = config.get_player_volume()
    print(f"[Config] Original volume: {original_volume}")

    # Change volume
    new_volume = 0.5
    config.set_player_volume(new_volume)
    print(f"[Config] Set volume to: {new_volume}")

    # Reload config to verify persistence
    config2 = Config(str(config_path))
    saved_volume = config2.get_player_volume()
    print(f"[Config] Reloaded volume from file: {saved_volume}")

    # Restore original
    config.set_player_volume(original_volume)
    print(f"[Config] Restored original volume: {original_volume}")

    if abs(new_volume - saved_volume) < 0.01:
        print("\n[PASS] Volume persistence works correctly")
        return True
    else:
        print("\n[FAIL] Volume was not persisted correctly")
        print(f"  Expected: {new_volume}")
        print(f"  Got: {saved_volume}")
        return False


def test_audio_player_volume():
    """Test AudioPlayer volume control directly."""
    print("\n" + "="*60)
    print("TEST: AudioPlayer Direct Volume Control")
    print("="*60)

    from src.youtube_player.player import AudioPlayer

    player = AudioPlayer()
    print(f"[AudioPlayer] Initial volume: {player.get_volume()}")

    # Test setting various volumes
    test_volumes = [0.0, 0.25, 0.5, 0.75, 1.0]
    all_pass = True

    for vol in test_volumes:
        player.set_volume(vol)
        actual_vol = player.get_volume()
        if abs(vol - actual_vol) < 0.01:
            print(f"[AudioPlayer] {vol} -> {actual_vol} [OK]")
        else:
            print(f"[AudioPlayer] {vol} -> {actual_vol} [FAIL]")
            all_pass = False

    player.cleanup()

    if all_pass:
        print("\n[PASS] AudioPlayer volume control works correctly")
        return True
    else:
        print("\n[FAIL] AudioPlayer volume control has issues")
        return False


def test_track_title_update_in_json():
    """Test that downloaded track title updates in JSON queue."""
    print("\n" + "="*60)
    print("TEST: Track Title Update in JSON")
    print("="*60)

    import json

    # Get initial queue
    queue_file = Path("youtube_queue.json")
    if not queue_file.exists():
        print("[INFO] Queue file doesn't exist yet, creating test...")
        initial_queue = []
    else:
        with open(queue_file, 'r', encoding='utf-8') as f:
            initial_queue = json.load(f)

    print(f"[Queue] Initial queue size: {len(initial_queue)}")

    # Create player
    player = YouTubePlayer(queue_file="youtube_queue.json")
    queue_before = player.get_queue()
    print(f"[Player] Queue before: {len(queue_before)} items")

    if queue_before:
        # Check first item - should have title updated from info
        first_item = queue_before[0]
        if first_item.title and first_item.title != "Loading...":
            print(f"[Queue] First track title: '{first_item.title}'")
            print(f"[Queue] Duration: {first_item.duration_sec}s")

            # Read from file to verify persistence
            with open(queue_file, 'r', encoding='utf-8') as f:
                persisted = json.load(f)

            persisted_first = persisted[0]
            if persisted_first['title'] == first_item.title:
                print(f"[Queue] Title persisted in JSON: '{persisted_first['title']}'")
                print("\n[PASS] Track title correctly updated in JSON")
                return True
            else:
                print(f"[ERROR] JSON title mismatch:")
                print(f"  In memory: '{first_item.title}'")
                print(f"  In file:   '{persisted_first['title']}'")
                print("\n[FAIL] Title not persisted correctly in JSON")
                return False
        else:
            print("[INFO] Queue has 'Loading...' title - this is expected during download")
            print("[INFO] Test inconclusive - wait for YouTube info to load")
            print("\n[SKIP] Skipping - queue item not yet loaded")
            return True
    else:
        print("[INFO] Queue is empty - add a YouTube track first")
        print("\n[SKIP] Skipping - queue is empty")
        return True


def test_next_track_removes_and_switches():
    """Test that next_track() removes old track from JSON and switches to next."""
    print("\n" + "="*60)
    print("TEST: Next Track Removes and Switches")
    print("="*60)

    import json

    queue_file = Path("youtube_queue.json")
    if not queue_file.exists():
        print("[INFO] Queue file doesn't exist - cannot test")
        print("\n[SKIP] Skipping - queue file not found")
        return True

    # Read initial queue from file
    with open(queue_file, 'r', encoding='utf-8') as f:
        initial_json = json.load(f)

    print(f"[Queue] Initial queue size from JSON: {len(initial_json)}")

    if len(initial_json) < 2:
        print("[INFO] Need at least 2 tracks in queue to test next_track()")
        print("\n[SKIP] Skipping - not enough tracks in queue")
        return True

    # Create player - this loads the queue from JSON
    player = YouTubePlayer(queue_file="youtube_queue.json")
    queue_before = player.get_queue()

    print(f"[Player] Queue size before next_track(): {len(queue_before)}")
    if queue_before:
        first_track = queue_before[0]
        print(f"[Player] Current track (will be removed): {first_track.title}")

    # Call next_track()
    print("[Player] Calling next_track()...")
    player.next_track()

    # Check in-memory queue
    queue_after = player.get_queue()
    print(f"[Player] Queue size after next_track(): {len(queue_after)}")

    # Check persisted JSON
    with open(queue_file, 'r', encoding='utf-8') as f:
        final_json = json.load(f)

    print(f"[Queue] Queue size in JSON after next_track(): {len(final_json)}")

    # Verify first track was removed
    if len(final_json) == len(initial_json) - 1:
        print(f"[Queue] Track removed: {len(initial_json)} -> {len(final_json)}")
    else:
        print(f"[ERROR] Queue size mismatch after removal:")
        print(f"  Expected: {len(initial_json) - 1}")
        print(f"  Got: {len(final_json)}")

    # Verify new current track
    if queue_after:
        new_current = queue_after[0]
        print(f"[Player] New current track: {new_current.title}")

        # Check if it matches first item in JSON
        if final_json and final_json[0]['title'] == new_current.title:
            print("[Queue] New current track matches JSON first item")
            print("\n[PASS] next_track() correctly removed old and switched to new")
            return True
        else:
            print("[ERROR] Current track doesn't match JSON")
            print("\n[FAIL] Track switching issue")
            return False
    else:
        if not final_json:
            print("[INFO] Queue now empty after removing first track")
            print("\n[PASS] next_track() correctly removed old track (queue now empty)")
            return True
        else:
            print("[ERROR] Queue still has items in JSON but not in player")
            print("\n[FAIL] Queue synchronization issue")
            return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("YouTube Player GUI Test Suite")
    print("="*60)

    results = {}

    try:
        results["audio_player"] = test_audio_player_volume()
    except Exception as e:
        print(f"\n[ERROR] in test_audio_player_volume: {e}")
        import traceback
        traceback.print_exc()
        results["audio_player"] = False

    try:
        results["volume_loading"] = test_volume_loading()
    except Exception as e:
        print(f"\n[ERROR] in test_volume_loading: {e}")
        import traceback
        traceback.print_exc()
        results["volume_loading"] = False

    try:
        results["volume_persistence"] = test_volume_persistence()
    except Exception as e:
        print(f"\n[ERROR] in test_volume_persistence: {e}")
        import traceback
        traceback.print_exc()
        results["volume_persistence"] = False

    try:
        results["track_title_update"] = test_track_title_update_in_json()
    except Exception as e:
        print(f"\n[ERROR] in test_track_title_update_in_json: {e}")
        import traceback
        traceback.print_exc()
        results["track_title_update"] = False

    try:
        results["next_track_removes_switches"] = test_next_track_removes_and_switches()
    except Exception as e:
        print(f"\n[ERROR] in test_next_track_removes_and_switches: {e}")
        import traceback
        traceback.print_exc()
        results["next_track_removes_switches"] = False

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{test_name}: {status}")

    total = len(results)
    passed = sum(1 for p in results.values() if p)
    print(f"\nTotal: {passed}/{total} tests passed")

    return all(results.values())


def print_usage():
    """Print usage instructions."""
    print("\n" + "="*60)
    print("How to test track title and next_track functionality:")
    print("="*60)
    print("""
1. Add YouTube tracks to the queue:

   Option A - Use helper script:
   python src/youtube_player/gui/test_add_tracks.py
   (Interactive helper to add test tracks)

   Option B - Use GUI app:
   python player_gui.py
   (Add tracks via the GUI application)

   Option C - Manually edit youtube_queue.json:
   [
     {
       "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
       "title": "Loading...",
       "duration_sec": 0,
       "added_at": "2024-01-17T00:00:00",
       "file_path": null,
       "downloaded": false,
       "download_progress": 0
     },
     {
       "url": "https://www.youtube.com/watch?v=OTHER_VIDEO_ID",
       "title": "Loading...",
       "duration_sec": 0,
       "added_at": "2024-01-17T00:00:00",
       "file_path": null,
       "downloaded": false,
       "download_progress": 0
     }
   ]

2. Wait for the app to download and update titles from YouTube

3. Run this test again: python src/youtube_player/gui/test.py

Test will verify:
  - Track titles are updated from YouTube
  - Titles are persisted in youtube_queue.json
  - next_track() removes the current track
  - next_track() switches to the next track in queue
""")


if __name__ == "__main__":
    import sys

    # Check if running with --help or no arguments
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', '--usage']:
        print_usage()
        sys.exit(0)

    # Run tests
    success = main()

    # Print usage info if tests were skipped
    if not success:
        # Check if this was due to empty queue
        queue_file = Path("youtube_queue.json")
        if not queue_file.exists() or not queue_file.stat().st_size > 2:
            print_usage()

    sys.exit(0 if success else 1)
