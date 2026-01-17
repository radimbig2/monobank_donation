import pygame
from pathlib import Path
from typing import Optional, Callable


class AudioPlayer:
    """Audio player using pygame."""

    def __init__(self):
        pygame.mixer.init()
        self._current_file: Optional[Path] = None
        self._is_playing = False
        self._is_paused = False
        self._volume = 0.7
        pygame.mixer.music.set_volume(self._volume)

    def play(self, file_path: Path) -> bool:
        """Play audio file."""
        try:
            if not file_path.exists():
                print(f"[AudioPlayer] File not found: {file_path}")
                return False

            pygame.mixer.music.load(str(file_path))
            pygame.mixer.music.play()
            self._current_file = file_path
            self._is_playing = True
            self._is_paused = False
            print(f"[AudioPlayer] Playing: {file_path.name}")
            return True
        except Exception as e:
            print(f"[AudioPlayer] Error playing: {e}")
            return False

    def pause(self) -> bool:
        """Pause playback."""
        if self._is_playing and not self._is_paused:
            try:
                pygame.mixer.music.pause()
                self._is_paused = True
                print("[AudioPlayer] Paused")
                return True
            except Exception as e:
                print(f"[AudioPlayer] Error pausing: {e}")
        return False

    def resume(self) -> bool:
        """Resume playback."""
        if self._is_paused:
            try:
                pygame.mixer.music.unpause()
                self._is_paused = False
                print("[AudioPlayer] Resumed")
                return True
            except Exception as e:
                print(f"[AudioPlayer] Error resuming: {e}")
        return False

    def stop(self) -> bool:
        """Stop playback."""
        if self._is_playing:
            try:
                pygame.mixer.music.stop()
                self._is_playing = False
                self._is_paused = False
                self._current_file = None
                print("[AudioPlayer] Stopped")
                return True
            except Exception as e:
                print(f"[AudioPlayer] Error stopping: {e}")
        return False

    def set_volume(self, volume: float) -> None:
        """Set volume (0.0 to 1.0)."""
        self._volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self._volume)
        print(f"[AudioPlayer] Volume: {int(self._volume * 100)}%")

    def get_volume(self) -> float:
        """Get current volume."""
        return self._volume

    def is_playing(self) -> bool:
        """Check if music is playing."""
        return pygame.mixer.music.get_busy() and self._is_playing

    def is_paused(self) -> bool:
        """Check if music is paused."""
        return self._is_paused

    def get_current_file(self) -> Optional[Path]:
        """Get currently playing file."""
        return self._current_file

    def get_position(self) -> float:
        """Get playback position in seconds."""
        if self._is_playing:
            return pygame.mixer.music.get_pos() / 1000.0
        return 0.0

    def cleanup(self) -> None:
        """Cleanup pygame mixer."""
        try:
            pygame.mixer.quit()
            print("[AudioPlayer] Cleaned up")
        except Exception as e:
            print(f"[AudioPlayer] Error cleaning up: {e}")
