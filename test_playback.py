#!/usr/bin/env python3
"""Test playback logic with debug information."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.youtube_player import YouTubePlayer
from src.youtube_player.player import AudioPlayer


def test_playback_logic():
    """Test the play/pause toggle logic."""
    print("\n" + "="*60)
    print("Playback Logic Test")
    print("="*60)

    # Create player
    player = YouTubePlayer(queue_file="youtube_queue.json")
    queue = player.get_queue()

    print(f"\n1. Queue Status:")
    print(f"   Total tracks: {len(queue)}")

    if not queue:
        print("   [ERROR] No tracks in queue!")
        return False

    current = player.get_current_track()
    print(f"\n2. Current Track:")
    print(f"   Title: {current.title}")
    print(f"   Downloaded: {current.downloaded}")
    print(f"   File path: {current.file_path}")
    print(f"   Duration: {current.duration_sec}s")

    if not current.downloaded:
        print("\n   [WARNING] Track is not downloaded!")
        print("   This is why music won't play.")
        print("   The app is waiting for YouTube to download the file.")
        return False

    if not current.file_path:
        print("\n   [WARNING] No file path set!")
        print("   The download might not have completed properly.")
        return False

    print(f"\n3. Audio Player Status (before play):")
    print(f"   Is playing: {player.player.is_playing()}")
    print(f"   Is paused: {player.player.is_paused()}")

    # Test play/pause toggle
    print(f"\n4. Testing pause() toggle (should start playing):")
    print(f"   Calling pause()...")
    result = player.pause()
    print(f"   Result: {result}")

    print(f"\n5. Audio Player Status (after pause() toggle):")
    print(f"   Is playing: {player.player.is_playing()}")
    print(f"   Is paused: {player.player.is_paused()}")

    if player.player.is_playing():
        print("\n   [SUCCESS] Music is playing!")
        print("   The pause() toggle is working correctly.")

        # Stop for cleanup
        player.player.stop()
        return True
    else:
        print("\n   [FAIL] Music is NOT playing!")
        print("   Check the logs above for errors.")
        return False


def test_audio_player_direct():
    """Test AudioPlayer directly with a real file."""
    print("\n" + "="*60)
    print("Direct AudioPlayer Test")
    print("="*60)

    # Find an existing MP3 file
    cache_dir = Path("youtube_cache")
    if not cache_dir.exists():
        print(f"\n[INFO] Cache directory doesn't exist: {cache_dir}")
        return False

    mp3_files = list(cache_dir.glob("*.mp3"))
    if not mp3_files:
        print(f"\n[INFO] No MP3 files in cache")
        return False

    test_file = mp3_files[0]
    print(f"\nTesting with: {test_file}")

    try:
        audio = AudioPlayer()
        print(f"\nAudioPlayer created")
        print(f"Initial volume: {audio.get_volume()}")

        print(f"\nAttempting to play: {test_file}")
        result = audio.play(test_file)
        print(f"Play result: {result}")

        import time
        time.sleep(2)  # Let it play for 2 seconds

        print(f"\nAfter 2 seconds:")
        print(f"Is playing: {audio.is_playing()}")
        print(f"Position: {audio.get_position()}s")

        audio.stop()
        print(f"Stopped")

        return audio.is_playing() == False

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    results = {}

    print("\nTesting YouTube Player Playback Logic")
    print("="*60)

    # Test 1: Queue and playback logic
    try:
        results["playback_logic"] = test_playback_logic()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        results["playback_logic"] = False

    # Test 2: Direct AudioPlayer test
    try:
        results["audio_player"] = test_audio_player_direct()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        results["audio_player"] = False

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Playback Logic: {'PASS' if results.get('playback_logic') else 'FAIL'}")
    print(f"AudioPlayer: {'PASS' if results.get('audio_player') else 'FAIL'}")

    if results.get("playback_logic"):
        print("\nConclusion: Playback logic is working!")
        print("If music still doesn't play in the GUI, check:")
        print("  1. Are tracks downloaded? (check youtube_cache/ folder)")
        print("  2. Is file_path set in youtube_queue.json?")
        print("  3. Are there errors in the console?")
    else:
        print("\nConclusion: Tracks need to be downloaded first")
        print("Run: python player_gui.py")
        print("Wait for tracks to download, then try clicking Play")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted")
    except Exception as e:
        print(f"\n[Error] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
