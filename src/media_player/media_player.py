import random
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config import Config

IMAGE_EXTENSIONS = {".gif", ".png", ".jpg", ".jpeg", ".webp"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a"}


@dataclass
class MediaSelection:
    image_path: str
    audio_path: str | None


class MediaPlayer:
    def __init__(self, config: "Config", project_root: Path | None = None):
        self._config = config
        self._project_root = project_root or Path.cwd()

        self._images: list[str] = []
        self._audio: list[str] = []

        self.reload_media_list()

    def _get_media_path(self) -> Path:
        """Get absolute path to media folder."""
        media_path = Path(self._config.get_media_path())
        if not media_path.is_absolute():
            media_path = self._project_root / media_path
        return media_path.resolve()

    def reload_media_list(self) -> None:
        """Scan media folder and reload file lists."""
        media_path = self._get_media_path()

        self._images = []
        self._audio = []

        if not media_path.exists():
            print(f"[MediaPlayer] Warning: Media path does not exist: {media_path}")
            return

        for file in media_path.rglob("*"):
            if file.is_file():
                # Get path relative to media folder
                rel_path = str(file.relative_to(media_path)).replace("\\", "/")
                ext = file.suffix.lower()

                if ext in IMAGE_EXTENSIONS:
                    self._images.append(rel_path)
                elif ext in AUDIO_EXTENSIONS:
                    self._audio.append(rel_path)

        print(f"[MediaPlayer] Found {len(self._images)} images, {len(self._audio)} audio files")

    def get_random_image(self) -> str | None:
        """Get random image from media folder."""
        if not self._images:
            return None
        return random.choice(self._images)

    def get_random_audio(self) -> str | None:
        """Get random audio from media folder."""
        if not self._audio:
            return None
        return random.choice(self._audio)

    def select_media(self, amount: int | None = None) -> MediaSelection | None:
        """
        Select media based on donation amount.
        If amount is None or no rules match, use random selection.
        Amount is in kopecks (1 UAH = 100 kopecks).
        """
        rules = self._config.get_media_rules()

        # Try to find matching rule
        if amount is not None and rules:
            for rule in rules:
                if rule.min_amount <= amount:
                    if rule.max_amount is None or amount <= rule.max_amount:
                        # Found matching rule
                        image = random.choice(rule.images) if rule.images else self.get_random_image()
                        audio = random.choice(rule.sounds) if rule.sounds else self.get_random_audio()

                        if image:
                            return MediaSelection(image_path=image, audio_path=audio)

        # Fallback to random selection
        image = self.get_random_image()
        if not image:
            return None

        return MediaSelection(
            image_path=image,
            audio_path=self.get_random_audio()
        )

    def get_all_images(self) -> list[str]:
        """Get list of all images."""
        return self._images.copy()

    def get_all_audio(self) -> list[str]:
        """Get list of all audio files."""
        return self._audio.copy()
