from .youtube_player import YouTubePlayer
from .player import AudioPlayer
from .queue_manager import QueueManager, QueueItem
from .youtube_downloader import YouTubeDownloader
from .url_parser import YouTubeURLParser
from .ui import PlayerUI

try:
    from .player_window import PlayerWindow
    HAS_GUI = True
except ImportError:
    HAS_GUI = False

__all__ = [
    "YouTubePlayer",
    "AudioPlayer",
    "QueueManager",
    "QueueItem",
    "YouTubeDownloader",
    "YouTubeURLParser",
    "PlayerUI",
    "HAS_GUI",
]

if HAS_GUI:
    __all__.append("PlayerWindow")
