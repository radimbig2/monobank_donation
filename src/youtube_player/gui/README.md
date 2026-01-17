# YouTube Player GUI Module

GUI interface for the YouTube Player using PyQt5.

## Features

- Play/Pause/Next track controls
- Volume control with persistence
- Queue display with download progress
- Track information (title, duration, current time)
- Configurable settings (loaded from config.yaml)

## Testing

### Quick Test (Mock Data)

Test with mock data without needing real YouTube downloads:

```bash
python src/youtube_player/gui/test_quick.py
```

This test:
- Creates mock tracks with real titles in the queue
- Verifies track titles are persisted in `youtube_queue.json`
- Verifies `next_track()` removes the current track
- Verifies `next_track()` switches to the next track in queue

### Full Test Suite

Run all GUI tests:

```bash
python src/youtube_player/gui/test.py
```

Tests include:
1. **AudioPlayer Direct Volume Control** - Verifies pygame volume control works
2. **Volume Loading from Config** - Checks config volume matches player volume
3. **Volume Persistence to Config** - Verifies volume changes are saved
4. **Track Title Update in JSON** - Checks downloaded track titles are persisted
5. **Next Track Removes and Switches** - Verifies track removal and switching

### Integration Test

For full integration testing with real YouTube downloads:

```bash
# Option 1: Use helper script to add test tracks
python src/youtube_player/gui/test_add_tracks.py

# Option 2: Use the GUI app directly
python player_gui.py
# Then run tests again:
python src/youtube_player/gui/test.py
```

## File Structure

```
src/youtube_player/gui/
├── __init__.py              # Module exports
├── player_window.py         # Main GUI window class
├── test.py                  # Full test suite
├── test_quick.py            # Quick test with mock data
├── test_add_tracks.py       # Helper to add test tracks
└── README.md                # This file
```

## Usage

The GUI is integrated with the main application:

```bash
# Standalone GUI (player_gui.py entry point)
python player_gui.py

# Full app with web server and GUI (main.py entry point)
python main.py

# CLI only (base.py entry point)
python base.py
```

## Architecture

The GUI module follows the project's modular architecture:

- **PlayerWindow**: Main GUI class (PyQt5.QMainWindow)
  - Manages UI layout (controls, queue, current track info)
  - Handles volume slider with persistence to config
  - Updates display every 500ms
  - Provides signals for async updates

- **PlayerSignals**: Custom Qt signals for cross-thread communication

## What Gets Tested

### Volume Control
- ✓ Volume slider responds to user input
- ✓ Volume loads from config on startup
- ✓ Volume changes persist to config.yaml
- ✓ Volume range is clamped to 0.0-1.0

### Queue Management
- ✓ Track titles are updated from YouTube
- ✓ Track titles are persisted in youtube_queue.json
- ✓ Download progress is tracked (0-100%)
- ✓ next_track() removes current track from queue
- ✓ next_track() switches to next available track
- ✓ Queue state is synchronized between memory and file

## Dependencies

- PyQt5 - GUI framework
- pygame - Audio playback
- yt-dlp - YouTube video info and download

## Known Issues

- Empty cache files show as errors when deleting after playback
- YouTube API may rate-limit requests for multiple tracks

## Future Improvements

- Add pause/resume visual feedback
- Add shuffle and repeat controls
- Add search functionality
- Add keyboard shortcuts
- Improve queue UI with drag-and-drop
