# Monobank Donation Tracker

A comprehensive donation tracking system for streamers that integrates with Monobank, displays donations in OBS overlays, and includes a built-in YouTube music player.

## 📑 Quick Navigation

- [Overview](#-overview)
- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Getting Started](#-getting-started)
- [Configuration](#️-configuration-guide)
- [OBS Setup](#-obs-setup)
- [Command Line Usage](#-command-line-usage)
- [Project Architecture](#️-project-architecture)
- [Documentation](#-documentation)
- [Development](#-development)
- [Troubleshooting](#-troubleshooting)
- [Monitoring](#-monitoring)
- [Support](#-support)

---

## 🎯 Overview

This application tracks donations from your Monobank account in real-time, displays them on stream via OBS browser sources, plays music from YouTube links mentioned in donation comments, and provides both a web interface and a GUI application for complete control.

**Perfect for:** Streamers, content creators, and anyone who accepts donations via Monobank.

---

## ✨ Features

### 1. **OBS Overlay Integration**
- Real-time donation notifications displayed on stream
- Customizable media (GIFs, videos) based on donation amount
- Sound effects for donations
- Transparent background for seamless overlay integration
- **URL:** `http://localhost:8080/`

### 2. **Donations Feed**
- Live list of recent donations with transparency for streaming
- Donor name, amount, and comments displayed
- Auto-updating when new donations arrive
- Large font for readability on stream
- **URL:** `http://localhost:8080/feed`

### 3. **YouTube Player**
- Automatically plays music from YouTube links in donation comments
- Downloads and caches videos (max 10 videos)
- Duration limit enforcement (videos must be < 10 minutes)
- CLI interface for console control
- Beautiful GUI application with visual controls
- Volume control with persistence

### 4. **Monobank API Integration**
- Real-time polling for new donations every N seconds
- Automatic donor name extraction from transactions
- Support for multiple donations in queue
- Interactive jar (account) selection on first run

### 5. **Dual Interface**
- **CLI Console:** Text-based control and information
- **GUI Application:** Beautiful PyQt5 interface with buttons and sliders
- Both run simultaneously and stay synchronized

---

## 📋 Requirements

- Python 3.9 or higher
- Monobank account with API token
- Dependencies:
  - `aiohttp` - Web server
  - `pyyaml` - Configuration
  - `yt-dlp` - YouTube downloads
  - `pygame` - Audio playback
  - `PyQt5` - GUI (optional, for visual interface)

---

## 🚀 Installation

### 1. Clone or download the project
```bash
git clone <repository-url>
cd free-monobank-hook
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Get your Monobank API token
1. Visit https://api.monobank.ua/
2. Generate an API token
3. Save it for configuration

### 4. Create configuration file
```bash
cp config.example.yaml config.yaml
```

### 5. Edit `config.yaml`
```yaml
server:
  port: 8080
  host: localhost

monobank:
  token: YOUR_MONOBANK_TOKEN_HERE
  jar_id: ""  # Leave empty for interactive selection on first run
  poll_interval: 60

media:
  path: ./media
  player_volume: 0.5

  rules:
    - min: 0
      max: 4999
      images: ["video/200.gif"]
      sounds: ["audio/sound.mp3"]
    - min: 5000
      max: 9999
      images: ["video/500.gif"]
      sounds: ["audio/sound.mp3"]
    - min: 10000
      images: ["video/premium.gif"]
      sounds: ["audio/sound.mp3"]

youtube_player:
  max_duration_seconds: 600  # 10 minutes max
  cache_dir: ./youtube_cache
  max_cached_videos: 10
```

---

## 🎮 Getting Started

### Quick Start (Recommended)

Run the main application with both CLI and GUI:
```bash
python main.py
```

This starts:
- Web server for OBS overlays
- Monobank donation polling
- YouTube player (CLI console)
- GUI application (visual controls)

### Console-Only Mode (For Servers)

If you're running on a server without a display:
```bash
python base.py
```

Includes everything except the GUI application.

### GUI Player Only

Run just the visual player (without web server and polling):
```bash
python player_gui.py
```

---

## ⚙️ Configuration Guide

### Media Rules

Configure what happens when donations of different amounts arrive:

```yaml
media:
  rules:
    - min: 0          # Donations from 0 UAH
      max: 4999       # Up to 49.99 UAH
      images: ["video/small.gif"]
      sounds: ["audio/ping.mp3"]

    - min: 5000       # 50 UAH and above
      max: 9999       # Up to 99.99 UAH
      images: ["video/medium.gif"]
      sounds: ["audio/notification.mp3"]

    - min: 10000      # 100 UAH and above
      images: ["video/large.gif"]
      sounds: ["audio/fanfare.mp3"]
```

**Note:** Amounts are in kopecks (1 UAH = 100 kopecks)

### Server Configuration

```yaml
server:
  port: 8080              # Web server port
  host: localhost         # Bind address
  show_test_button: false # Show test button on overlay
```

### YouTube Player Settings

```yaml
youtube_player:
  max_duration_seconds: 600   # Max video length (seconds)
  cache_dir: ./youtube_cache  # Where to save downloaded videos
  max_cached_videos: 10       # Maximum videos to keep cached
```

---

## 🎬 OBS Setup

### Adding to OBS

Add the following browser sources to your OBS scene:

#### 1. Donation Overlay (Full Screen)
- **URL:** `http://localhost:8080/`
- **Width:** 1920
- **Height:** 1080
- **Position:** Full scene or custom placement
- **Interaction:** Disabled

#### 2. Donations Feed (Side Panel)
- **URL:** `http://localhost:8080/feed`
- **Width:** 400
- **Height:** 1080
- **Position:** Corner of scene
- **Interaction:** Disabled

Both will automatically update when donations arrive.

---

## 💻 Command Line Usage

### Main Console Commands

When running `main.py`, you can:
- **Press Enter** - Send a test donation (for testing)
- **See donation logs** - Real-time updates in console

### YouTube Player Commands

In the CLI interface:

| Command | Function |
|---------|----------|
| `p` | Play/Pause |
| `n` | Next track |
| `v+` | Increase volume (+10%) |
| `v-` | Decrease volume (-10%) |
| `q` | Show queue |
| `c` | Show current track |
| `s` | Exit player |
| `?` | Show help |

### GUI Controls

- **Play/Pause Button** - Toggle playback
- **Next Button** - Skip to next track
- **Volume Slider** - Adjust volume
- **Queue List** - See upcoming tracks

---

## 🏗️ Project Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────┐
│         MonobankClient (API Integration)            │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│         DonationPoller (Polling Service)            │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│      NotificationService (Main Orchestrator)        │
└──┬─────────────────────────────────────────────┬───┘
   │                                             │
   v                                             v
┌──────────────────────┐         ┌────────────────────────┐
│   WebHost (Server)   │         │  YouTubePlayer (Music) │
└──────────────────────┘         └────────────────────────┘
   │                                    │
   v                                    v
┌──────────────────────┐         ┌────────────────────────┐
│   OBS Overlays       │         │   GUI Application      │
└──────────────────────┘         └────────────────────────┘
```

### Module Structure

```
src/
├── config/              # Configuration management
│   ├── config.py
│   └── test.py
├── web_host/            # HTTP server and WebSocket
│   ├── web_host.py
│   └── test.py
├── media_player/        # Media selection by amount
│   ├── media_player.py
│   └── test.py
├── notification/        # Notification service
│   ├── notification_service.py
│   └── test.py
├── monobank/            # Monobank API client
│   ├── monobank_client.py
│   └── test.py
├── poller/              # Donation polling
│   ├── donation_poller.py
│   └── test.py
├── donations_feed/      # Donations stream feed
│   ├── donations_feed.py
│   └── test.py
└── youtube_player/      # YouTube player
    ├── player.py
    ├── ui.py            # CLI interface
    ├── youtube_player.py
    ├── youtube_downloader.py
    ├── queue_manager.py
    └── gui/
        ├── player_window.py
        └── test.py
```

---

## 🔧 Development

### Running Tests

Each module has a `test.py` file for testing:

```bash
# Test configuration
python src/config/test.py

# Test YouTube player
python src/youtube_player/test.py

# Test web server
python src/web_host/test.py
```

### Code Standards

As per project guidelines:
- Comments in English only
- Use type hints whenever possible
- Write clean, maintainable code
- Each module in separate directory with tests

---

## 🐛 Troubleshooting

### Application won't start

**Error: "Config file not found"**
```bash
cp config.example.yaml config.yaml
```

**Error: "Monobank token not configured"**
- Edit `config.yaml`
- Add your token from https://api.monobank.ua/

### GUI not working

**PyQt5 not installed:**
```bash
pip install PyQt5
```

### No donations arriving

**Check these:**
1. Token is correct in `config.yaml`
2. Jar ID is properly selected
3. Check console logs for "[DonationPoller]" messages
4. Poll interval is set to reasonable value (60 seconds recommended)

### YouTube player issues

**No sound:**
- Ensure pygame is installed: `pip install pygame`
- Check that `./youtube_cache/` directory exists
- Verify video duration is less than configured limit

**Tracks not downloading:**
- Check internet connection
- Verify YouTube URL in donation comment is valid
- Check that `./youtube_cache/` is writable
- Look for error messages in console

### Music not playing in OBS

- Add the audio from system mixer to OBS
- Or use separate audio input device
- Check that volume is not muted

---

## 📊 Monitoring

### Console Output

The application shows real-time information:

```
[Main] Monobank integration enabled
[Main] YouTube player initialized
[Main] Polling for donations every 60 seconds

[DonationPoller] Checking for new transactions...
[Donation] New donation: John - 100.00 UAH - "Love your stream!"
[YouTube Player] Added track: "Song Name" (5:30)
```

### Logs

Important log prefixes:
- `[Main]` - Main application events
- `[DonationPoller]` - Donation polling events
- `[Donation]` - New donations
- `[Player]` - YouTube player events
- `[WebHost]` - Web server events
- `[MonobankClient]` - API errors

---

## 🤝 Integration with OBS

### Browser Source Settings

For best compatibility:

**Overlay Settings:**
- Refresh browser when scene becomes active: ✓
- Use GPU acceleration: ✓
- Custom CSS: Add any custom styling needed
- Shutdown source when not visible: ✓

**Feed Settings:**
- Same as overlay
- Position in corner for minimal impact

### Recommended Scene Layout

```
┌─────────────────────────────────────┐
│           Main Gameplay             │
│                                     │
│        [Donation Overlay]           │
│                                     │
└─────────────────────────────────────┤
│[Donation Feed]   [Other Elements]   │
└─────────────────────────────────────┘
```

---

## 📚 Documentation

For detailed technical documentation, see:

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Complete technical architecture, data flow, design patterns, and system overview
- **[CLASS_REFERENCE.md](CLASS_REFERENCE.md)** - Comprehensive reference for all 20+ classes with fields, methods, and descriptions

---

## 🔗 Additional Resources

- **Monobank API Docs:** https://api.monobank.ua/
- **yt-dlp Documentation:** https://github.com/yt-dlp/yt-dlp
- **PyQt5 Documentation:** https://doc.qt.io/qt-5/
- **aiohttp Documentation:** https://docs.aiohttp.org/

---

## 📝 License

See LICENSE file for details.

---

## 🆘 Support

If you encounter issues:

1. Check the Troubleshooting section above
2. Review console logs for error messages
3. Ensure all requirements are installed: `pip install -r requirements.txt`
4. Try running with fresh config: `cp config.example.yaml config.yaml`

---

## 🎉 Quick Reference

### Most Common Tasks

**Make it work on startup:**
```bash
python main.py
```

**Run on server without GUI:**
```bash
python base.py
```

**Send test donation:**
```
Press Enter in console
```

**Change OBS URL:**
Update `server.port` in `config.yaml`

**Add media for donations:**
1. Place files in `./media/video/` and `./media/audio/`
2. Update `media.rules` in `config.yaml`

**Configure donation amounts:**
Edit `media.rules` in `config.yaml` with min/max amounts in kopecks.

---

## 🚀 Quick Links

| What are you looking for? | Go to |
|---------------------------|-------|
| 📖 Full system architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
| 📚 API class reference | [CLASS_REFERENCE.md](CLASS_REFERENCE.md) |
| ⚙️ Configuration examples | [Installation section](#-installation) |
| 🎮 How to use | [Getting Started section](#-getting-started) |
| 🐛 Something not working? | [Troubleshooting section](#-troubleshooting) |

---

**Made with ❤️ for streamers**
