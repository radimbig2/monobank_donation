import sys
import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSlider, QListWidget, QListWidgetItem, QProgressBar
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont

if TYPE_CHECKING:
    from .youtube_player import YouTubePlayer


class PlayerSignals(QObject):
    """Signals for player updates."""
    update_current = pyqtSignal(str, int, int)  # title, current_duration, total_duration
    update_queue = pyqtSignal()
    update_status = pyqtSignal(str)  # status message
    update_volume = pyqtSignal(int)  # volume percentage


class PlayerWindow(QMainWindow):
    """GUI window for YouTube player."""

    def __init__(self, player: "YouTubePlayer"):
        super().__init__()
        self.player = player
        self.signals = PlayerSignals()

        # Setup UI
        self.setWindowTitle("🎵 YouTube Player")
        self.setGeometry(100, 100, 600, 700)

        # Connect signals
        self.signals.update_current.connect(self._on_update_current)
        self.signals.update_queue.connect(self._on_update_queue)
        self.signals.update_status.connect(self._on_update_status)
        self.signals.update_volume.connect(self._on_update_volume)

        # Create main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # Main layout
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Current track section
        layout.addWidget(self._create_current_track_section())

        # Controls section
        layout.addWidget(self._create_controls_section())

        # Queue section
        layout.addWidget(self._create_queue_section())

        # Status bar
        self.status_label = QLabel("Готово")
        self.status_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.status_label)

        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_display)
        self.update_timer.start(500)

        self.show()

    def _create_current_track_section(self) -> QWidget:
        """Create current track display section."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Title
        self.title_label = QLabel("Нет трека")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.title_label.setFont(font)
        self.title_label.setWordWrap(True)
        layout.addWidget(self.title_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Time labels
        time_layout = QHBoxLayout()
        self.current_time_label = QLabel("0:00")
        self.total_time_label = QLabel("0:00")
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(self.total_time_label)
        layout.addLayout(time_layout)

        return widget

    def _create_controls_section(self) -> QWidget:
        """Create playback controls section."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Playback buttons
        btn_layout = QHBoxLayout()

        self.play_pause_btn = QPushButton("▶ Включить")
        self.play_pause_btn.clicked.connect(self._toggle_play)
        self.play_pause_btn.setMinimumHeight(40)
        btn_layout.addWidget(self.play_pause_btn)

        self.next_btn = QPushButton("⏭ Следующий")
        self.next_btn.clicked.connect(self._next_track)
        self.next_btn.setMinimumHeight(40)
        btn_layout.addWidget(self.next_btn)

        layout.addLayout(btn_layout)

        # Volume control
        vol_layout = QHBoxLayout()
        vol_layout.addWidget(QLabel("🔊"))

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(int(self.player.player.get_volume() * 100))
        self.volume_slider.sliderMoved.connect(self._on_volume_changed)
        vol_layout.addWidget(self.volume_slider)

        self.volume_label = QLabel("70%")
        self.volume_label.setMinimumWidth(35)
        vol_layout.addWidget(self.volume_label)

        layout.addLayout(vol_layout)

        return widget

    def _create_queue_section(self) -> QWidget:
        """Create queue display section."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Title
        queue_title = QLabel("📋 Очередь")
        font = QFont()
        font.setPointSize(11)
        font.setBold(True)
        queue_title.setFont(font)
        layout.addWidget(queue_title)

        # Queue list
        self.queue_list = QListWidget()
        self.queue_list.setMaximumHeight(250)
        layout.addWidget(self.queue_list)

        return widget

    def _toggle_play(self) -> None:
        """Toggle play/pause."""
        current = self.player.get_current_track()

        if not current:
            self.signals.update_status.emit("Нет трека в очереди")
            return

        if not current.downloaded:
            self.signals.update_status.emit("Трек ещё загружается...")
            return

        # Toggle pause/play
        self.player.pause()
        self.signals.update_status.emit("Пауза включена" if self.player.player.is_paused() else "Воспроизведение")

    def _next_track(self) -> None:
        """Skip to next track."""
        queue = self.player.get_queue()
        if not queue:
            self.signals.update_status.emit("Очередь пуста")
            return

        self.player.next_track()
        self.signals.update_queue.emit()
        self.signals.update_status.emit("Перешли на следующий трек")

    def _on_volume_changed(self, value: int) -> None:
        """Handle volume slider change."""
        volume = value / 100.0
        self.player.set_volume(volume)
        self.volume_label.setText(f"{value}%")

    def _update_display(self) -> None:
        """Update display every 500ms."""
        current = self.player.get_current_track()

        if current:
            self.title_label.setText(current.title)

            # Update progress
            if self.player.is_playing():
                pos = self.player.player.get_position()
                if current.duration_sec > 0:
                    progress = int((pos / current.duration_sec) * 100)
                    self.progress_bar.setValue(progress)

                    # Update time labels
                    current_min = int(pos) // 60
                    current_sec = int(pos) % 60
                    self.current_time_label.setText(f"{current_min}:{current_sec:02d}")

            # Total time
            total_min = current.duration_sec // 60
            total_sec = current.duration_sec % 60
            self.total_time_label.setText(f"{total_min}:{total_sec:02d}")

            # Update button
            if self.player.player.is_paused():
                self.play_pause_btn.setText("▶ Включить")
            else:
                self.play_pause_btn.setText("⏸ Пауза")
        else:
            self.title_label.setText("Очередь пуста")
            self.progress_bar.setValue(0)
            self.current_time_label.setText("0:00")
            self.total_time_label.setText("0:00")
            self.play_pause_btn.setText("▶ Включить")

        # Update queue display
        self._update_queue_display()

    def _update_queue_display(self) -> None:
        """Update queue list display."""
        queue = self.player.get_queue()

        # Always update to show latest info
        self.queue_list.clear()

        for i, item in enumerate(queue):
            minutes = item.duration_sec // 60
            seconds = item.duration_sec % 60

            # Format based on status
            if item.downloaded:
                status = "✓"
                progress_str = ""
            else:
                status = "⏳"
                progress = item.download_progress if hasattr(item, 'download_progress') else 0
                progress_str = f" [{progress}%]" if progress > 0 else ""

            text = f"{i+1}. {status} {item.title[:40]} ({minutes}:{seconds:02d}){progress_str}"
            widget_item = QListWidgetItem(text)

            if i == 0:
                # Highlight current track
                widget_item.setBackground(self.palette().mid())

            self.queue_list.addItem(widget_item)

    def _on_update_current(self, title: str, current_duration: int, total_duration: int) -> None:
        """Handle current track update signal."""
        self.title_label.setText(title)
        self.current_time_label.setText(f"{current_duration // 60}:{current_duration % 60:02d}")
        self.total_time_label.setText(f"{total_duration // 60}:{total_duration % 60:02d}")

    def _on_update_queue(self) -> None:
        """Handle queue update signal."""
        self._update_queue_display()

    def _on_update_status(self, status: str) -> None:
        """Handle status update signal."""
        self.status_label.setText(status)

    def _on_update_volume(self, volume: int) -> None:
        """Handle volume update signal."""
        self.volume_slider.setValue(volume)
        self.volume_label.setText(f"{volume}%")

    def closeEvent(self, event) -> None:
        """Handle window close."""
        self.update_timer.stop()
        event.accept()
