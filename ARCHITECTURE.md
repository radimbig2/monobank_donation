# Architecture - Monobank Donation Tracker

Complete technical architecture documentation for the free-monobank-hook project.

---

## System Overview

The application is a donation tracking system that integrates with Monobank, displays donations via OBS overlays, and includes a YouTube music player. It uses async/await for concurrency and WebSocket for real-time updates.

```
┌────────────────────────────────────────────────────────────┐
│              Monobank API (External Service)              │
└──────────────────────────┬─────────────────────────────────┘
                           │
┌──────────────────────────▼─────────────────────────────────┐
│            DonationPoller (Polling Service)                │
│  - Periodically fetches transactions from Monobank         │
│  - Filters new donations and calls callbacks               │
└──────────────────────────┬─────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
┌─────────────────┐  ┌──────────────────┐  ┌───────────────┐
│   Notification  │  │  DonationsFeed   │  │ YouTubePlayer │
│    Service      │  │  (WebSocket)     │  │  (Async)      │
└────────┬────────┘  └────────┬─────────┘  └───────────────┘
         │                    │
         └────────┬───────────┘
                  │
┌─────────────────▼────────────────────────────────┐
│          WebHost (HTTP Server)                  │
│  - Serves overlay HTML with media               │
│  - Manages WebSocket connections                │
│  - Broadcasts donation updates                  │
└──────────────────┬───────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
    ┌────────┐            ┌──────────┐
    │  OBS   │            │ Browser  │
    │Overlay │            │  (Feed)  │
    └────────┘            └──────────┘
```

---

## Module Breakdown

### 1. **src/config/**

**Purpose:** Configuration management and parsing.

**Files:**
- `config.py` - Main configuration class

**Key Classes:**
- `ServerConfig` - Server settings (port, host, volume)
- `MonobankConfig` - Monobank API credentials and polling
- `MediaConfig` - Media rules and paths
- `MediaRule` - Single media rule (min/max amount, images, sounds)
- `Config` - Main config manager with YAML parsing

**Responsibilities:**
- Load configuration from `config.yaml`
- Parse and validate all settings
- Provide getter/setter methods for configuration values
- Save changes back to file (for jar_id and volume)

---

### 2. **src/web_host/**

**Purpose:** HTTP server for OBS overlays and real-time updates.

**Files:**
- `web_host.py` - Main web server class

**Key Classes:**
- `WebHost` - aiohttp web server

**Routes:**
- `GET /` - Overlay HTML page
- `GET /ws` - Overlay WebSocket connection
- `POST /test-donation` - Test donation button
- `GET /feed` - Donations feed page
- `GET /feed/ws` - Feed WebSocket connection
- `GET /static/*` - Static files (CSS, JS)
- `GET /media/*` - Media files (GIFs, sounds)

**Key Methods:**
- `start_async()` / `stop_async()` - Server lifecycle
- `show_image()` - Display image for duration
- `show_media()` - Display image + audio with donation info
- `clear()` - Clear current display
- `_broadcast()` - Send message to all WebSocket clients

**Features:**
- WebSocket support for real-time updates
- Static file serving
- Media path resolution
- Test donation endpoint

---

### 3. **src/media_player/**

**Purpose:** Media selection based on donation amount.

**Files:**
- `media_player.py` - Media selection engine

**Key Classes:**
- `MediaSelection` - Result containing image and audio paths
- `MediaPlayer` - Media file manager and selector

**Key Methods:**
- `select_media(amount)` - Find media matching donation amount
- `get_random_image()` / `get_random_audio()` - Random selection
- `reload_media_list()` - Scan media folder
- `get_all_images()` / `get_all_audio()` - List all media

**Features:**
- Amount-based media selection via rules
- Fallback to random selection
- Media folder scanning
- Support for GIF, PNG, JPG, MP3, WAV, etc.

---

### 4. **src/notification/**

**Purpose:** Donation notifications and display orchestration.

**Files:**
- `notification_service.py` - Notification service

**Key Classes:**
- `Donation` - Donation data (amount, comment, donor name, timestamp)
- `NotificationService` - Displays donations with media

**Key Methods:**
- `notify()` - Show notification immediately
- `queue_notification()` - Add to queue for sequential display
- `test_donation()` - Send test donation
- `_process_queue()` - Process queued notifications
- `start()` / `stop()` - Service lifecycle

**Features:**
- Async notification queue
- Sequential display (one at a time)
- Media selection and display
- WebSocket updates to feed
- Test donation support

---

### 5. **src/monobank/**

**Purpose:** Monobank API integration.

**Files:**
- `monobank_client.py` - API client

**Key Classes:**
- `JarInfo` - Jar (account) information
- `JarTransaction` - Transaction data (donation)
- `MonobankClient` - API client wrapper

**Key Methods:**
- `get_jars()` - List all jars
- `get_jar_by_id()` - Get specific jar
- `get_jar_transactions()` - Get transactions for jar
- `get_jar_balance()` - Get current balance
- `_request()` - Internal API request handler

**Features:**
- API token authentication
- Transaction filtering (incoming only)
- Donor name extraction from description
- Amount conversion (kopecks to UAH)

---

### 6. **src/poller/**

**Purpose:** Periodic donation polling and notification.

**Files:**
- `donation_poller.py` - Polling service

**Key Classes:**
- `DonationPoller` - Async polling service

**Key Methods:**
- `start()` / `stop()` - Polling lifecycle
- `poll_once()` - Manual poll
- `on_new_donation()` - Register callback
- `_poll_loop()` - Main polling loop
- `_initial_load()` - Load recent transactions to mark as seen

**Features:**
- Async polling at configurable interval
- Duplicate detection via transaction ID tracking
- Callback support (sync and async)
- Initial load to avoid showing old donations

---

### 7. **src/donations_feed/**

**Purpose:** Real-time donations feed broadcasting.

**Files:**
- `donations_feed.py` - Feed manager

**Key Classes:**
- `DonationsFeed` - WebSocket broadcast manager

**Key Methods:**
- `add_donation()` - Add donation to feed
- `register_websocket()` / `unregister_websocket()` - Client management
- `broadcast_new_donation()` - Send to all clients
- `_broadcast()` - Internal broadcast helper
- `get_donations()` - Get current list
- `clear()` - Clear all donations

**Features:**
- Max donations limit (keeps recent only)
- WebSocket client tracking
- Broadcast to all connected clients
- JSON serialization

---

### 8. **src/youtube_player/**

**Purpose:** YouTube music player with queue management.

**Submodules:**
- `youtube_player.py` - Main player
- `queue_manager.py` - Queue persistence
- `youtube_downloader.py` - yt-dlp wrapper
- `url_parser.py` - YouTube URL extraction
- `player.py` - Audio playback (pygame)
- `ui.py` - CLI interface
- `gui/` - PyQt5 GUI application

**Key Classes:**

#### YouTubePlayer
- Main orchestrator managing queue, downloads, playback

**Key Methods:**
- `add_from_comment()` - Extract and add URL from text
- `start()` / `stop()` - Lifecycle
- `pause()` / `resume()` - Playback control
- `next_track()` - Skip to next
- `set_volume()` - Volume control
- `get_current_track()` / `get_queue()` - Queue access
- `_playback_loop()` - Main playback loop
- `_download_next_items()` - Download queue items

**Features:**
- Auto-download of queued videos
- Duration validation (< 10 minutes)
- Concurrent download management
- Auto-play next when track finishes
- Cache management

#### QueueManager
- Persistent queue stored in JSON

**Key Methods:**
- `load()` / `save()` - JSON file I/O
- `add()` / `remove()` - Queue manipulation
- `get_next()` / `get_all()` - Queue access
- `mark_downloaded()` - Mark as downloaded
- `update_item_info()` / `update_progress()` - Item updates

#### QueueItem (dataclass)
- `url` - YouTube URL
- `title` - Video title
- `duration_sec` - Duration in seconds
- `file_path` - Local file path after download
- `downloaded` - Download status
- `download_progress` - Progress 0-100

#### YouTubeDownloader
- yt-dlp wrapper for downloads

**Key Methods:**
- `get_info()` - Get title and duration
- `download()` - Download audio to MP3
- `is_valid_length()` - Check if video is <= 10 minutes
- `cleanup_cache()` - Remove old cache files
- `get_cache_size()` - Cache file count

#### YouTubeURLParser
- Extract and validate YouTube URLs

**Key Methods:**
- `extract_url()` - Find URL in text
- `extract_video_id()` - Get video ID from URL

#### AudioPlayer
- pygame audio playback

**Key Methods:**
- `play()` - Play file
- `pause()` / `resume()` - Playback control
- `stop()` - Stop playback
- `set_volume()` / `get_volume()` - Volume control
- `is_playing()` / `is_paused()` - Status
- `get_position()` - Current position
- `cleanup()` - Cleanup mixer

#### PlayerUI (CLI Interface)
- Text-based control interface

**Key Methods:**
- `start()` / `stop()` - Lifecycle
- `_ui_loop()` - Main input loop
- `_toggle_pause()` - P command
- `_next_track()` - N command
- `_volume_up()` / `_volume_down()` - V+ / V- commands
- `_show_queue()` - Q command
- `_show_current()` - C command
- `_print_help()` - ? command

#### PlayerWindow (GUI)
- PyQt5 GUI application

**Key Widgets:**
- Play/Pause button
- Next button
- Volume slider
- Queue list
- Status label
- Progress bar

**Key Methods:**
- `_toggle_play()` - Play/pause control
- `_next_track()` - Next track
- `_on_volume_changed()` - Volume slider
- `_update_display()` - Update all UI elements
- `_update_queue_display()` - Update queue list

---

## Data Flow

### Donation Flow

```
1. Monobank (External)
   ↓
2. DonationPoller.poll_once()
   - Fetches transactions
   - Filters new ones
   ↓
3. Callbacks triggered
   - YouTubePlayer.add_from_comment()
   ↓
4. NotificationService.queue_notification()
   - Adds to queue
   ↓
5. NotificationService._process_queue()
   - Processes one by one
   - Calls notify()
   ↓
6. MediaPlayer.select_media()
   - Selects image + audio
   ↓
7. WebHost.show_media()
   - Broadcasts to overlay
   ↓
8. DonationsFeed.broadcast_new_donation()
   - Broadcasts to feed
   ↓
9. Browser WebSocket clients receive updates
```

### YouTube Flow

```
1. Donation comment with URL
   ↓
2. YouTubePlayer.add_from_comment()
   - Parses URL
   - Validates length
   - Adds to queue
   ↓
3. QueueManager.add()
   - Saves to JSON
   ↓
4. YouTubePlayer._download_next_items()
   - Downloads audio
   - Marks as downloaded
   ↓
5. YouTubePlayer._playback_loop()
   - Monitors playback
   - Auto-plays next
   ↓
6. AudioPlayer.play()
   - Pygame playback
```

---

## Key Design Patterns

### 1. **Async Architecture**
- All I/O operations are async (Monobank API, downloads)
- `asyncio.Queue` for thread-safe notification queuing
- `asyncio.Task` for background loops

### 2. **Separation of Concerns**
- Each module handles one responsibility
- Clear interfaces between components
- Configuration is centralized

### 3. **Observer Pattern**
- `on_new_donation()` callbacks
- WebSocket broadcasting
- Decoupled notification handlers

### 4. **Persistence**
- Config in YAML
- Queue in JSON
- Cache in filesystem

### 5. **Graceful Degradation**
- Missing media falls back to random
- No URL in comment → skip
- Download error → queue waits
- No file → skip playback

---

## Configuration Flow

```
config.yaml (YAML file)
    ↓
Config.reload() (Parse YAML)
    ↓
ServerConfig / MonobankConfig / MediaConfig
    ↓
Getter methods (get_port, get_jar_id, etc.)
    ↓
Application uses config
```

---

## Concurrency Model

### Main Thread
- Entry point (main.py or base.py)
- Starts async event loop in thread

### Async Event Loop (Thread 1)
- Web server (aiohttp)
- Monobank polling
- Notification queue processing
- YouTube downloads

### Optional GUI Event Loop (Thread 2 or Main)
- PyQt5 event loop
- Shares queue with async loop via JSON file

### Input Listener (Thread N)
- Console input for test donations

---

## Error Handling

### API Errors
- Retry on network error (silent)
- Log API errors in console
- Continue operation with degraded functionality

### Download Errors
- Keep item in queue (still shows in list)
- Log download failure
- Continue to next item

### File Errors
- Skip missing media files
- Use random fallback
- Log path issues

### Parse Errors
- Validation at boundaries only
- Assume internal code is correct
- Only validate user input and external data

---

## File Structure

```
free-monobank-hook/
├── main.py                          # Main entry point (CLI + GUI)
├── base.py                          # CLI only
├── player_gui.py                    # GUI only
├── config.yaml                      # User configuration
├── config.example.yaml              # Config template
├── youtube_queue.json               # YouTube queue (auto-created)
├── youtube_cache/                   # Downloaded MP3s
│
├── src/
│   ├── __init__.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config.py               # Configuration classes
│   │   └── test.py                 # Config tests
│   │
│   ├── web_host/
│   │   ├── __init__.py
│   │   ├── web_host.py             # HTTP server
│   │   ├── static/                 # CSS, JS files
│   │   ├── templates/              # HTML templates
│   │   └── test.py                 # Web server tests
│   │
│   ├── media_player/
│   │   ├── __init__.py
│   │   ├── media_player.py         # Media selection
│   │   └── test.py                 # Tests
│   │
│   ├── notification/
│   │   ├── __init__.py
│   │   ├── notification_service.py # Notification queue
│   │   └── test.py                 # Tests
│   │
│   ├── monobank/
│   │   ├── __init__.py
│   │   ├── monobank_client.py      # Monobank API
│   │   └── test.py                 # Tests
│   │
│   ├── poller/
│   │   ├── __init__.py
│   │   ├── donation_poller.py      # Polling service
│   │   └── test.py                 # Tests
│   │
│   ├── donations_feed/
│   │   ├── __init__.py
│   │   ├── donations_feed.py       # WebSocket feed
│   │   ├── static/                 # Feed CSS, JS
│   │   ├── templates/              # Feed HTML
│   │   └── test.py                 # Tests
│   │
│   └── youtube_player/
│       ├── __init__.py
│       ├── youtube_player.py       # Main player
│       ├── queue_manager.py        # Queue persistence
│       ├── youtube_downloader.py   # Download wrapper
│       ├── url_parser.py           # URL extraction
│       ├── player.py               # Audio playback
│       ├── ui.py                   # CLI interface
│       ├── test.py                 # Tests
│       └── gui/
│           ├── __init__.py
│           ├── player_window.py    # PyQt5 GUI
│           └── test.py             # GUI tests
│
├── media/                          # User's media files
│   ├── video/                      # GIFs, videos
│   └── audio/                      # Sounds
│
├── requirements.txt                # Dependencies
├── README.md                        # User guide
├── ARCHITECTURE.md                 # This file
└── CLASS_REFERENCE.md              # Class documentation
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Web** | aiohttp | HTTP server, WebSocket |
| **GUI** | PyQt5 | Desktop interface |
| **Audio** | pygame | Playback control |
| **Downloader** | yt-dlp | YouTube downloads |
| **Config** | PyYAML | Configuration parsing |
| **Async** | asyncio | Concurrency |
| **Data** | dataclasses | Type-safe data structures |

---

## Performance Considerations

### Memory
- Queue stored in JSON (loads at startup)
- Media files list cached in memory
- Seen transaction IDs stored in memory

### Network
- API polling at configurable interval (60s default)
- WebSocket connections are persistent
- Downloads are sequential (one at a time)

### CPU
- Async operations (non-blocking)
- No busy-wait loops (use sleep/events)
- pygame mixer handles audio efficiently

### Storage
- YouTube cache size limited (max 10 files)
- Config file small (YAML)
- Queue file grows with usage (manual cleanup if needed)

---

## Extension Points

### Add Custom Notification Handlers
```python
poller.on_new_donation(my_custom_handler)
```

### Add Media Rules
Edit config.yaml media.rules section

### Custom Overlays
Edit web_host/templates/overlay.html

### Custom Audio Format
Modify YouTubeDownloader audio format settings

---

## Testing

Each module includes `test.py` with:
- Unit tests
- Manual testing interface
- Debug utilities

Run tests:
```bash
python src/config/test.py
python src/youtube_player/test.py
python src/web_host/test.py
```

---

**Last Updated:** 2025-01-17
