# Class Reference - Monobank Donation Tracker

Complete reference for all classes in the project with fields, methods, and descriptions.

---

## src/config/config.py

### ServerConfig
**Type:** `@dataclass`
**Purpose:** Stores server configuration settings.

**Fields:**
- `port: int = 8080` - HTTP server port
- `host: str = "localhost"` - Server host address
- `show_test_button: bool = True` - Show test button on overlay
- `player_volume: float = 0.7` - Default player volume (0.0-1.0)

---

### MonobankConfig
**Type:** `@dataclass`
**Purpose:** Stores Monobank API credentials and polling settings.

**Fields:**
- `token: str = ""` - Monobank API token
- `jar_id: str = ""` - Target jar ID for donations
- `poll_interval: int = 60` - Polling interval in seconds

---

### MediaRule
**Type:** `@dataclass`
**Purpose:** Defines media selection rule based on donation amount.

**Fields:**
- `min_amount: int` - Minimum donation amount (kopecks)
- `max_amount: int | None` - Maximum donation amount (kopecks), None for unlimited
- `images: list[str] = field(default_factory=list)` - Image file paths
- `sounds: list[str] = field(default_factory=list)` - Audio file paths

---

### MediaConfig
**Type:** `@dataclass`
**Purpose:** Stores media configuration.

**Fields:**
- `path: str = "./media"` - Path to media folder
- `default_duration: int = 5000` - Default display duration (milliseconds)
- `rules: list[MediaRule] = field(default_factory=list)` - Media selection rules

---

### Config
**Type:** Regular class
**Purpose:** Main configuration manager - loads, parses, and provides access to all settings.

**Fields (Private):**
- `_config_path: Path` - Path to config.yaml file
- `_raw: dict[str, Any]` - Raw YAML content
- `_server: ServerConfig` - Parsed server config
- `_monobank: MonobankConfig` - Parsed Monobank config
- `_media: MediaConfig` - Parsed media config

**Constructor:**
```python
def __init__(self, config_path: str = "config.yaml") -> None
```
- Loads and parses configuration file
- Initializes all config objects

**Methods:**

#### Public
```python
def reload(self) -> None
```
- Reloads configuration from file
- Called automatically on initialization

```python
def get_port(self) -> int
```
- Returns server port

```python
def get_host(self) -> str
```
- Returns server host address

```python
def show_test_button(self) -> bool
```
- Returns whether test button should be shown

```python
def get_player_volume(self) -> float
```
- Returns player volume (0.0-1.0)

```python
def get_monobank_token(self) -> str
```
- Returns Monobank API token

```python
def get_jar_id(self) -> str
```
- Returns target jar ID

```python
def get_poll_interval(self) -> int
```
- Returns polling interval in seconds

```python
def get_media_path(self) -> str
```
- Returns path to media folder

```python
def get_default_duration(self) -> int
```
- Returns default display duration (milliseconds)

```python
def get_media_rules(self) -> list[MediaRule]
```
- Returns list of media rules

```python
def set_jar_id(self, jar_id: str) -> None
```
- Sets jar_id and saves to file
- Called during interactive setup

```python
def set_player_volume(self, volume: float) -> None
```
- Sets player volume (clamped to 0.0-1.0)
- Saves to file

#### Private
```python
def _parse_server(self) -> None
```
- Parses server section from YAML

```python
def _parse_monobank(self) -> None
```
- Parses monobank section from YAML

```python
def _parse_media(self) -> None
```
- Parses media section from YAML

```python
def _save(self) -> None
```
- Saves raw config to YAML file

---

## src/web_host/web_host.py

### WebHost
**Type:** Regular class
**Purpose:** HTTP server handling OBS overlays and WebSocket connections.

**Fields (Private):**
- `_config: Config` - Configuration reference
- `_app: web.Application | None` - aiohttp application instance
- `_runner: web.AppRunner | None` - aiohttp runner
- `_site: web.TCPSite | None` - aiohttp TCP site
- `_websockets: weakref.WeakSet[web.WebSocketResponse]` - Connected WebSocket clients
- `_running: bool` - Server running state
- `_notification_service: NotificationService | None` - Notification service reference
- `_donations_feed: DonationsFeed | None` - Donations feed reference
- `_static_dir: Path` - Static files directory
- `_templates_dir: Path` - HTML templates directory
- `_feed_static_dir: Path` - Feed static files directory
- `_feed_templates_dir: Path` - Feed templates directory
- `_project_root: Path` - Project root directory

**Constructor:**
```python
def __init__(self, config: Config, project_root: Path | None = None) -> None
```
- Initializes server with configuration
- Sets up directory paths

**Methods:**

#### Public - Lifecycle
```python
async def start_async(self) -> None
```
- Starts HTTP server asynchronously
- Sets up routes and binds to port

```python
async def stop_async(self) -> None
```
- Stops HTTP server asynchronously
- Closes all WebSocket connections

```python
def start(self) -> None
```
- Synchronous wrapper for start_async

```python
def stop(self) -> None
```
- Synchronous wrapper for stop_async

```python
def is_running(self) -> bool
```
- Returns True if server is running

```python
def get_url(self) -> str
```
- Returns server URL (e.g., "http://localhost:8080")

#### Public - Configuration
```python
def set_notification_service(self, service: NotificationService) -> None
```
- Sets notification service for test donations

```python
def set_donations_feed(self, feed: DonationsFeed) -> None
```
- Sets donations feed for updates

#### Public - Display Methods
```python
async def show_image(self, image_path: str, duration_ms: int | None = None) -> None
```
- Displays image on overlay for specified duration
- Broadcasts via WebSocket to all clients

```python
async def show_gif(self, gif_path: str, duration_ms: int | None = None) -> None
```
- Alias for show_image (GIFs handled same way)

```python
async def show_media(
    self,
    image_path: str,
    audio_path: str | None = None,
    duration_ms: int | None = None,
    donor_name: str | None = None,
    comment: str | None = None,
    amount: int | None = None,
) -> None
```
- Displays image + audio with donation information
- Broadcasts to all WebSocket clients with metadata

```python
async def clear(self) -> None
```
- Clears current display on overlay

#### Private - Routing
```python
def _setup_routes(self, app: web.Application) -> None
```
- Configures all HTTP routes

#### Private - Request Handlers
```python
async def _handle_index(self, request: web.Request) -> web.Response
```
- Serves overlay HTML page
- Injects show_test_button configuration

```python
async def _handle_test_donation(self, request: web.Request) -> web.Response
```
- Handles test donation button click
- Returns JSON response

```python
async def _handle_websocket(self, request: web.Request) -> web.WebSocketResponse
```
- Handles overlay WebSocket connection
- Tracks connected clients

```python
async def _handle_feed_index(self, request: web.Request) -> web.Response
```
- Serves donations feed HTML page

```python
async def _handle_feed_websocket(self, request: web.Request) -> web.WebSocketResponse
```
- Handles feed WebSocket connection
- Delegates to donations feed

#### Private - Broadcasting
```python
async def _broadcast(self, message: dict) -> None
```
- Sends JSON message to all WebSocket clients
- Handles disconnection errors gracefully

---

## src/media_player/media_player.py

### MediaSelection
**Type:** `@dataclass`
**Purpose:** Result of media selection containing file paths.

**Fields:**
- `image_path: str` - Path to image file
- `audio_path: str | None` - Path to audio file (optional)

---

### MediaPlayer
**Type:** Regular class
**Purpose:** Selects and manages media files based on donation rules.

**Fields (Private):**
- `_config: Config` - Configuration reference
- `_project_root: Path` - Project root directory
- `_images: list[str]` - List of available image files
- `_audio: list[str]` - List of available audio files

**Constructor:**
```python
def __init__(self, config: Config, project_root: Path | None = None) -> None
```
- Initializes media player
- Scans media folder for files

**Methods:**

#### Public
```python
def reload_media_list(self) -> None
```
- Rescans media folder
- Updates internal file lists
- Logs found files

```python
def get_random_image(self) -> str | None
```
- Returns random image from available images
- Returns None if no images found

```python
def get_random_audio(self) -> str | None
```
- Returns random audio from available audio files
- Returns None if no audio found

```python
def select_media(self, amount: int | None = None) -> MediaSelection | None
```
- Selects media based on donation amount (kopecks)
- Matches against configured rules
- Falls back to random selection if no rule matches
- Returns None if no media available

```python
def get_all_images(self) -> list[str]
```
- Returns copy of all available image paths

```python
def get_all_audio(self) -> list[str]
```
- Returns copy of all available audio paths

#### Private
```python
def _get_media_path(self) -> Path
```
- Resolves media folder path
- Handles relative paths

---

## src/notification/notification_service.py

### Donation
**Type:** `@dataclass`
**Purpose:** Represents a single donation.

**Fields:**
- `amount: int` - Donation amount in kopecks (1 UAH = 100 kopecks)
- `currency: str = "UAH"` - Currency code
- `comment: str | None = None` - Donor comment
- `timestamp: datetime = field(default_factory=datetime.now)` - Donation timestamp
- `donor_name: str | None = None` - Name of donor

**Properties:**
```python
@property
def amount_uah(self) -> float
```
- Returns amount converted to UAH

**Methods:**
```python
def __str__(self) -> str
```
- Returns formatted donation string (for logging)

---

### NotificationService
**Type:** Regular class
**Purpose:** Manages donation notifications and orchestrates display.

**Fields (Private):**
- `_web_host: WebHost` - Web server reference
- `_media_player: MediaPlayer` - Media player reference
- `_config: Config` - Configuration reference
- `_donations_feed: DonationsFeed | None` - Donations feed reference
- `_queue: asyncio.Queue[Donation]` - Notification queue
- `_processing: bool` - Processing loop state
- `_process_task: asyncio.Task | None` - Processing task

**Constructor:**
```python
def __init__(
    self,
    web_host: WebHost,
    media_player: MediaPlayer,
    config: Config,
) -> None
```
- Initializes notification service
- Creates notification queue

**Methods:**

#### Public - Lifecycle
```python
async def start(self) -> None
```
- Starts notification processing loop
- Safe to call multiple times

```python
async def stop(self) -> None
```
- Stops notification processing loop
- Cancels processing task

#### Public - Notification Methods
```python
async def notify(self, donation: Donation) -> None
```
- Shows notification immediately
- Selects media, broadcasts to overlay
- Updates donations feed

```python
async def queue_notification(self, donation: Donation) -> None
```
- Adds donation to queue for sequential processing
- Logs queue size

```python
async def test_donation(self, amount: int = 10000) -> None
```
- Creates and shows test donation
- Default amount: 100 UAH (10000 kopecks)

```python
def get_queue_size(self) -> int
```
- Returns current queue size

#### Public - Integration
```python
def set_donations_feed(self, feed: DonationsFeed) -> None
```
- Sets donations feed for broadcasting

#### Private
```python
async def _process_queue(self) -> None
```
- Main queue processing loop
- Displays notifications sequentially
- Respects display duration
- Continues until stopped

---

## src/monobank/monobank_client.py

### JarInfo
**Type:** `@dataclass`
**Purpose:** Represents a Monobank jar (account).

**Fields:**
- `id: str` - Jar unique ID
- `send_id: str` - Send ID for transactions
- `title: str` - Jar name
- `description: str` - Jar description
- `currency_code: int` - ISO 4217 currency code (980 = UAH)
- `balance: int` - Balance in kopecks
- `goal: int | None` - Goal in kopecks (None if no goal)

**Properties:**
```python
@property
def balance_uah(self) -> float
```
- Returns balance in UAH

```python
@property
def goal_uah(self) -> float | None
```
- Returns goal in UAH or None

---

### JarTransaction
**Type:** `@dataclass`
**Purpose:** Represents a single transaction (donation).

**Fields:**
- `id: str` - Transaction unique ID
- `time: datetime` - Transaction timestamp
- `amount: int` - Amount in kopecks (positive = incoming)
- `description: str` - Transaction description
- `comment: str | None` - Donor comment
- `donor_name: str | None = None` - Extracted donor name

**Properties:**
```python
@property
def amount_uah(self) -> float
```
- Returns amount in UAH

**Static Methods:**
```python
@staticmethod
def parse_donor_name(description: str) -> str | None
```
- Extracts donor name from transaction description
- Looks for "Від: Name" pattern
- Returns None if not found

---

### MonobankClient
**Type:** Regular class
**Purpose:** Wrapper for Monobank API.

**Fields (Private):**
- `_config: Config` - Configuration reference
- `_token: str` - API token from config

**Constructor:**
```python
def __init__(self, config: Config) -> None
```
- Initializes client with configuration

**Methods:**

#### Public
```python
async def get_client_info(self) -> dict
```
- Gets client information from API
- Returns raw API response (includes jars, accounts)

```python
async def get_jars(self) -> list[JarInfo]
```
- Returns list of all jars for the account

```python
async def get_jar_by_id(self, jar_id: str) -> JarInfo | None
```
- Returns specific jar by ID
- Returns None if not found

```python
async def get_statements(
    self,
    account_id: str,
    from_time: int,
    to_time: int | None = None,
) -> list[dict]
```
- Gets account statements (raw API response)
- Timestamps are Unix timestamps
- Returns raw transaction dictionaries

```python
async def get_jar_transactions(
    self,
    jar_id: str | None = None,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
) -> list[JarTransaction]
```
- Gets transactions for a jar
- Uses jar_id from config if not provided
- Filters only incoming (positive) transactions
- Extracts donor names automatically
- Default from_time: last hour

```python
async def get_jar_balance(self, jar_id: str | None = None) -> int
```
- Gets current jar balance in kopecks
- Uses jar_id from config if not provided

#### Private
```python
def _get_headers(self) -> dict
```
- Returns HTTP headers with API token

```python
async def _request(self, endpoint: str) -> dict | list
```
- Makes GET request to Monobank API
- Returns parsed JSON response
- Raises exception on error

---

## src/poller/donation_poller.py

### DonationPoller
**Type:** Regular class
**Purpose:** Periodically polls Monobank for new donations.

**Fields (Private):**
- `_monobank: MonobankClient` - Monobank client
- `_notification: NotificationService` - Notification service
- `_config: Config` - Configuration reference
- `_running: bool` - Polling loop state
- `_poll_task: asyncio.Task | None` - Polling task
- `_seen_tx_ids: set[str]` - IDs of already seen transactions
- `_callbacks: list[Callable[[Donation], Any]]` - New donation callbacks
- `_last_poll: datetime | None` - Timestamp of last poll

**Constructor:**
```python
def __init__(
    self,
    monobank_client: MonobankClient,
    notification_service: NotificationService,
    config: Config,
) -> None
```
- Initializes poller
- Sets up callback list and state

**Methods:**

#### Public - Lifecycle
```python
async def start(self) -> None
```
- Starts polling service
- Performs initial load to mark transactions as seen
- Creates polling task

```python
async def stop(self) -> None
```
- Stops polling service
- Cancels polling task

```python
def is_running(self) -> bool
```
- Returns True if polling is active

#### Public - Callbacks
```python
def on_new_donation(self, callback: Callable[[Donation], None]) -> None
```
- Registers callback for new donations
- Supports both sync and async callbacks

#### Public - Manual Operations
```python
async def poll_once(self) -> list[Donation]
```
- Performs manual poll for testing

```python
def get_seen_count(self) -> int
```
- Returns number of seen transaction IDs

```python
def clear_seen(self) -> None
```
- Clears seen transactions (for testing)

#### Private
```python
async def _initial_load(self) -> None
```
- Loads recent transactions (last hour)
- Marks them as seen to avoid replay

```python
async def _poll_loop(self) -> None
```
- Main polling loop
- Polls at configured interval
- Handles errors gracefully

```python
async def _poll_once(self) -> list[Donation]
```
- Internal poll implementation
- Gets new transactions
- Calls callbacks for new donations

---

## src/donations_feed/donations_feed.py

### DonationsFeed
**Type:** Regular class
**Purpose:** Manages donations list and broadcasts to WebSocket clients.

**Fields (Private):**
- `_config: Config` - Configuration reference
- `_max_donations: int` - Maximum donations to keep
- `_donations: list[Donation]` - List of recent donations
- `_websockets: weakref.WeakSet` - Connected WebSocket clients

**Constructor:**
```python
def __init__(self, config: Config, max_donations: int = 50) -> None
```
- Initializes donations feed
- Sets maximum donations limit

**Methods:**

#### Public
```python
def add_donation(self, donation: Donation) -> None
```
- Adds donation to feed
- Maintains max_donations limit
- Logs update

```python
async def register_websocket(self, ws: web.WebSocketResponse) -> None
```
- Registers new WebSocket client
- Sends current donations list

```python
def unregister_websocket(self, ws: web.WebSocketResponse) -> None
```
- Unregisters WebSocket client

```python
async def broadcast_new_donation(self, donation: Donation) -> None
```
- Broadcasts new donation to all clients

```python
def get_donations(self) -> list[Donation]
```
- Returns copy of donations list

```python
def clear(self) -> None
```
- Clears all donations

#### Private
```python
async def _send_current_donations(self, ws: web.WebSocketResponse) -> None
```
- Sends current donations to new client

```python
async def _broadcast(self, message: dict) -> None
```
- Broadcasts JSON message to all clients

```python
@staticmethod
def _donation_to_dict(donation: Donation) -> dict
```
- Converts donation to JSON-serializable dict

---

## src/youtube_player/youtube_player.py

### YouTubePlayer
**Type:** Regular class
**Purpose:** Main YouTube player orchestrator.

**Fields (Private):**
- `parser: YouTubeURLParser` - URL parser
- `queue: QueueManager` - Queue manager
- `downloader: YouTubeDownloader` - Downloader
- `player: AudioPlayer` - Audio player
- `_current_index: Optional[int]` - Current queue index
- `_running: bool` - Running state
- `_playback_task: Optional[asyncio.Task]` - Playback task
- `_auto_play: bool` - Auto-play next track
- `_was_playing: bool` - Previous playback state

**Constructor:**
```python
def __init__(self, queue_file: str = "youtube_queue.json") -> None
```
- Initializes player
- Loads queue from file

**Methods:**

#### Public - Lifecycle
```python
async def start(self) -> None
```
- Starts player
- Downloads queued items
- Starts playback loop

```python
async def stop(self) -> None
```
- Stops player
- Disables auto-play
- Cancels playback task

```python
def cleanup(self) -> None
```
- Cleans up audio player resources

#### Public - Content
```python
async def add_from_comment(self, comment: str) -> bool
```
- Extracts YouTube URL from comment
- Validates length (< 10 minutes)
- Adds to queue
- Starts download
- Returns True if added

```python
def get_current_track(self) -> Optional[QueueItem]
```
- Returns next track in queue

```python
def get_queue(self) -> list[QueueItem]
```
- Returns copy of all queued items

```python
def is_playing(self) -> bool
```
- Returns True if audio is currently playing

#### Public - Playback Control
```python
def pause(self) -> bool
```
- Toggles play/pause
- Enables/disables auto-play
- Returns success status

```python
def resume(self) -> bool
```
- Resumes playback
- Enables auto-play

```python
def next_track(self) -> None
```
- Skips to next track
- Removes current from queue
- Deletes audio file
- Enables auto-play

```python
def set_volume(self, volume: float) -> None
```
- Sets volume (0.0-1.0)

#### Private
```python
async def _download_next_items(self, max_downloads: int = 10) -> None
```
- Downloads queued items up to limit
- Updates progress

```python
async def _playback_loop(self) -> None
```
- Main playback monitoring loop
- Auto-plays next when current finishes
- Respects auto-play flag

---

## src/youtube_player/queue_manager.py

### QueueItem
**Type:** `@dataclass`
**Purpose:** Single item in YouTube queue.

**Fields:**
- `url: str` - YouTube URL
- `title: str = ""` - Video title
- `duration_sec: int = 0` - Duration in seconds
- `added_at: str = field(default_factory=...)` - ISO timestamp when added
- `file_path: Optional[str] = None` - Local file path after download
- `downloaded: bool = False` - Download status
- `download_progress: int = 0` - Progress 0-100

---

### QueueManager
**Type:** Regular class
**Purpose:** Manages persistent YouTube queue storage.

**Fields (Private):**
- `queue_file: Path` - Path to JSON queue file
- `_queue: list[QueueItem]` - In-memory queue

**Constructor:**
```python
def __init__(self, queue_file: str = "youtube_queue.json") -> None
```
- Initializes queue manager
- Loads queue from file

**Methods:**

#### Public
```python
def load(self) -> None
```
- Loads queue from JSON file
- Handles missing/corrupted files gracefully

```python
def save(self) -> None
```
- Saves queue to JSON file
- Pretty-printed with indentation

```python
def add(self, item: QueueItem) -> None
```
- Adds item to queue
- Saves to file

```python
def remove(self, index: int) -> Optional[QueueItem]
```
- Removes item at index
- Saves to file
- Returns removed item or None

```python
def get_next(self) -> Optional[QueueItem]
```
- Returns first item in queue (next to play)
- Returns None if empty

```python
def get_all(self) -> list[QueueItem]
```
- Returns copy of all items

```python
def clear(self) -> None
```
- Clears entire queue
- Saves to file

```python
def size(self) -> int
```
- Returns number of items in queue

```python
def mark_downloaded(self, index: int, file_path: str) -> bool
```
- Marks item as downloaded
- Sets file path and progress to 100%
- Saves to file
- Returns success

```python
def update_item_info(self, index: int, title: str = None, duration_sec: int = None) -> bool
```
- Updates item title and duration
- Saves to file
- Returns success

```python
def update_progress(self, index: int, progress: int) -> bool
```
- Updates download progress (0-100)
- Clamps to valid range
- Doesn't save (in-memory only)

```python
def get_downloaded_count(self) -> int
```
- Returns count of downloaded items

---

## src/youtube_player/youtube_downloader.py

### YouTubeDownloader
**Type:** Regular class
**Purpose:** Downloads YouTube videos using yt-dlp.

**Class Fields:**
- `MAX_DURATION_SEC = 600` - Maximum allowed duration (10 minutes)
- `CACHE_DIR = Path("./youtube_cache")` - Cache directory

**Constructor:**
```python
def __init__(self) -> None
```
- Creates cache directory if needed

**Methods:**

#### Public
```python
async def get_info(self, url: str) -> Optional[Tuple[str, int]]
```
- Gets video title and duration
- Runs yt-dlp asynchronously
- Returns (title, duration_in_seconds) or None on error
- Timeout: 10 seconds

```python
async def download(self, url: str, video_id: str) -> Optional[Path]
```
- Downloads audio from YouTube video
- Saves as MP3 in cache directory
- Returns Path to file or None on error
- Checks duration before downloading
- Returns cached file if already exists

```python
async def is_valid_length(self, url: str) -> bool
```
- Checks if video duration <= 10 minutes
- Returns False if info unavailable

```python
def cleanup_cache(self, max_files: int = 10) -> None
```
- Removes oldest files if cache exceeds max_files
- Logs removed files

```python
def get_cache_size(self) -> int
```
- Returns count of MP3 files in cache

---

## src/youtube_player/url_parser.py

### YouTubeURLParser
**Type:** Regular class
**Purpose:** Extracts and validates YouTube URLs from text.

**Class Fields:**
- `PATTERNS: list[str]` - Regex patterns for YouTube URLs

**Static Methods:**

```python
@staticmethod
def extract_url(text: str) -> Optional[str]
```
- Extracts YouTube URL from comment text
- Supports youtube.com, youtu.be, music.youtube.com
- Returns full URL or None if not found

```python
@staticmethod
def extract_video_id(url: str) -> Optional[str]
```
- Extracts video ID from YouTube URL
- Returns video ID or None if invalid

---

## src/youtube_player/player.py

### AudioPlayer
**Type:** Regular class
**Purpose:** Audio playback using pygame mixer.

**Fields (Private):**
- `_current_file: Optional[Path]` - Currently playing file
- `_is_playing: bool` - Playback state
- `_is_paused: bool` - Pause state
- `_volume: float` - Current volume (0.0-1.0)

**Constructor:**
```python
def __init__(self) -> None
```
- Initializes pygame mixer
- Sets default volume to 0.7

**Methods:**

#### Public - Playback Control
```python
def play(self, file_path: Path) -> bool
```
- Plays audio file
- Stops previous playback
- Returns success status

```python
def pause(self) -> bool
```
- Pauses playback
- Returns success status

```python
def resume(self) -> bool
```
- Resumes paused playback
- Returns success status

```python
def stop(self) -> bool
```
- Stops playback
- Returns success status

#### Public - Volume Control
```python
def set_volume(self, volume: float) -> None
```
- Sets volume (clamped to 0.0-1.0)
- Logs current volume percentage

```python
def get_volume(self) -> float
```
- Returns current volume

#### Public - Status
```python
def is_playing(self) -> bool
```
- Returns True if audio is playing

```python
def is_paused(self) -> bool
```
- Returns True if audio is paused

```python
def get_current_file(self) -> Optional[Path]
```
- Returns path of currently playing file

```python
def get_position(self) -> float
```
- Returns playback position in seconds

#### Public - Cleanup
```python
def cleanup(self) -> None
```
- Quits pygame mixer
- Called on shutdown

---

## src/youtube_player/ui.py

### PlayerUI
**Type:** Regular class
**Purpose:** Text-based CLI interface for YouTube player.

**Class Fields:**
- `COMMANDS: dict[str, str]` - Command help text

**Fields (Private):**
- `player: YouTubePlayer` - Player reference
- `_running: bool` - UI loop state

**Constructor:**
```python
def __init__(self, player: YouTubePlayer) -> None
```
- Initializes UI with player

**Methods:**

#### Public - Lifecycle
```python
def start(self) -> None
```
- Starts UI in separate daemon thread
- Displays help message

```python
def stop(self) -> None
```
- Stops UI loop

#### Private - Main Loop
```python
def _ui_loop(self) -> None
```
- Main input loop running in separate thread
- Processes commands

#### Private - Command Handlers
```python
def _toggle_pause(self) -> None
```
- P command - toggle play/pause

```python
def _next_track(self) -> None
```
- N command - skip to next track

```python
def _volume_up(self) -> None
```
- V+ command - increase volume by 10%

```python
def _volume_down(self) -> None
```
- V- command - decrease volume by 10%

```python
def _show_queue(self) -> None
```
- Q command - display queue

```python
def _show_current(self) -> None
```
- C command - display current track

```python
def _print_help(self) -> None
```
- ? command - display help

---

## src/youtube_player/gui/player_window.py

### PlayerSignals
**Type:** Regular class (inherits QObject)
**Purpose:** PyQt5 signals for GUI updates.

**Signals:**
```python
update_current = pyqtSignal(str, int, int)  # title, current_duration, total_duration
update_queue = pyqtSignal()
update_status = pyqtSignal(str)  # status message
update_volume = pyqtSignal(int)  # volume percentage
```

---

### PlayerWindow
**Type:** Regular class (inherits QMainWindow)
**Purpose:** PyQt5 GUI for YouTube player.

**Fields (Public/Protected):**
- `player: YouTubePlayer` - Player reference
- `config: Optional[Config]` - Configuration reference
- `signals: PlayerSignals` - Signal emitter
- `status_label: QLabel` - Status display
- `title_label: QLabel` - Current track title
- `play_pause_btn: QPushButton` - Play/Pause button
- `next_btn: QPushButton` - Next button
- `volume_slider: QSlider` - Volume control
- `volume_label: QLabel` - Volume percentage display
- `queue_list: QListWidget` - Queue list display
- `progress_bar: QProgressBar` - Playback progress
- `current_time_label: QLabel` - Current position
- `total_time_label: QLabel` - Total duration
- `update_timer: QTimer` - Display update timer

**Constructor:**
```python
def __init__(self, player: YouTubePlayer, config: Optional[Config] = None) -> None
```
- Initializes window
- Creates all UI elements
- Connects signals and slots
- Loads volume from config if available

**Methods:**

#### Private - UI Creation
```python
def _create_current_track_section(self) -> QWidget
```
- Creates track display section

```python
def _create_controls_section(self) -> QWidget
```
- Creates buttons and volume control

```python
def _create_queue_section(self) -> QWidget
```
- Creates queue list display

#### Private - Event Handlers
```python
def _toggle_play(self) -> None
```
- Handles play/pause button click

```python
def _next_track(self) -> None
```
- Handles next button click

```python
def _on_volume_changed(self, value: int) -> None
```
- Handles volume slider change
- Saves to config if available

```python
def _update_display(self) -> None
```
- Updates all UI elements every 500ms
- Called by update_timer

```python
def _update_queue_display(self) -> None
```
- Updates queue list display

```python
def _on_update_current(self, title: str, current_duration: int, total_duration: int) -> None
```
- Signal slot for current track update

```python
def _on_update_queue(self) -> None
```
- Signal slot for queue update

```python
def _on_update_status(self, status: str) -> None
```
- Signal slot for status message

```python
def _on_update_volume(self, volume: int) -> None
```
- Signal slot for volume update

```python
def closeEvent(self, event) -> None
```
- Handles window close event

---

## Constants and Type Definitions

### src/media_player/media_player.py
```python
IMAGE_EXTENSIONS = {".gif", ".png", ".jpg", ".jpeg", ".webp"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a"}
```

### src/youtube_player/youtube_downloader.py
```python
MAX_DURATION_SEC = 10 * 60  # 10 minutes = 600 seconds
CACHE_DIR = Path("./youtube_cache")
```

### src/youtube_player/youtube_downloader.py (yt-dlp options)
```python
# Download format: best audio
# Audio format: MP3 at 192 kbps
# Output: {video_id}.mp3 in cache
```

---

## Inheritance Hierarchy

### QObject Hierarchy (PyQt5)
```
QObject
  └── PlayerSignals (custom signals)
```

### QMainWindow Hierarchy (PyQt5)
```
QWidget
  └── QMainWindow
      └── PlayerWindow (custom GUI)
```

---

## Key Design Patterns Used

### 1. **Dataclass Pattern**
- `ServerConfig`, `MonobankConfig`, `MediaConfig`
- `MediaRule`, `Donation`, `JarInfo`, `JarTransaction`, `QueueItem`
- `MediaSelection`

### 2. **Async/Await Pattern**
- `DonationPoller`, `NotificationService`, `YouTubePlayer`, `YouTubeDownloader`
- `WebHost`, `MonobankClient`

### 3. **Observer Pattern**
- `DonationPoller.on_new_donation()` callbacks
- PyQt5 signals in `PlayerSignals`

### 4. **Singleton-like Pattern**
- `Config`, `AudioPlayer`
- Shared instances throughout application

### 5. **Facade Pattern**
- `YouTubePlayer` aggregates:
  - `YouTubeURLParser`
  - `QueueManager`
  - `YouTubeDownloader`
  - `AudioPlayer`
  - `PlayerUI`

---

**Last Updated:** 2025-01-17
