import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class QueueItem:
    """Item in YouTube queue."""
    url: str
    title: str = ""
    duration_sec: int = 0  # Duration in seconds
    added_at: str = field(default_factory=lambda: datetime.now().isoformat())
    file_path: Optional[str] = None  # Local file path after download
    downloaded: bool = False


class QueueManager:
    """Manage YouTube queue persistence."""

    def __init__(self, queue_file: str = "youtube_queue.json"):
        self.queue_file = Path(queue_file)
        self._queue: list[QueueItem] = []
        self.load()

    def load(self) -> None:
        """Load queue from file."""
        if self.queue_file.exists():
            try:
                with open(self.queue_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._queue = [QueueItem(**item) for item in data]
                print(f"[QueueManager] Loaded {len(self._queue)} items from queue")
            except Exception as e:
                print(f"[QueueManager] Error loading queue: {e}")
                self._queue = []
        else:
            self._queue = []

    def save(self) -> None:
        """Save queue to file."""
        try:
            with open(self.queue_file, "w", encoding="utf-8") as f:
                json.dump([asdict(item) for item in self._queue], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[QueueManager] Error saving queue: {e}")

    def add(self, item: QueueItem) -> None:
        """Add item to queue."""
        self._queue.append(item)
        self.save()
        print(f"[QueueManager] Added: {item.title} ({item.duration_sec}s)")

    def remove(self, index: int) -> Optional[QueueItem]:
        """Remove item from queue by index."""
        if 0 <= index < len(self._queue):
            item = self._queue.pop(index)
            self.save()
            print(f"[QueueManager] Removed: {item.title}")
            return item
        return None

    def get_next(self) -> Optional[QueueItem]:
        """Get next item in queue."""
        return self._queue[0] if self._queue else None

    def get_all(self) -> list[QueueItem]:
        """Get all items in queue."""
        return self._queue.copy()

    def clear(self) -> None:
        """Clear entire queue."""
        self._queue.clear()
        self.save()
        print("[QueueManager] Queue cleared")

    def size(self) -> int:
        """Get queue size."""
        return len(self._queue)

    def mark_downloaded(self, index: int, file_path: str) -> bool:
        """Mark item as downloaded."""
        if 0 <= index < len(self._queue):
            self._queue[index].downloaded = True
            self._queue[index].file_path = file_path
            self.save()
            return True
        return False

    def get_downloaded_count(self) -> int:
        """Get count of downloaded items."""
        return sum(1 for item in self._queue if item.downloaded)
