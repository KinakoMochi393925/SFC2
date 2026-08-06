"""音声プレビュー用ウィジェット。"""
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget


def _format_ms(ms: int) -> str:
    total_seconds = max(0, ms) // 1000
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"


class AudioPreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)

        self._play_button = QPushButton("再生")
        self._pause_button = QPushButton("一時停止")
        self._stop_button = QPushButton("停止")
        self._seek_slider = QSlider(Qt.Orientation.Horizontal)
        self._position_label = QLabel("00:00 / 00:00")

        self._play_button.clicked.connect(self._player.play)
        self._pause_button.clicked.connect(self._player.pause)
        self._stop_button.clicked.connect(self._player.stop)

        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)

        self._seeking = False
        self._seek_slider.sliderPressed.connect(lambda: setattr(self, "_seeking", True))
        self._seek_slider.sliderReleased.connect(self._on_slider_released)

        icon_label = QLabel("♪ 音声ファイル")
        icon_label.setStyleSheet("font-size: 16px; color: #555555;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        controls = QHBoxLayout()
        controls.addWidget(self._play_button)
        controls.addWidget(self._pause_button)
        controls.addWidget(self._stop_button)
        controls.addWidget(self._seek_slider)
        controls.addWidget(self._position_label)

        layout = QVBoxLayout(self)
        layout.addWidget(icon_label, stretch=1)
        layout.addLayout(controls)

    def load(self, file_path: str) -> None:
        self.stop()
        self._player.setSource(QUrl.fromLocalFile(file_path))

    def stop(self) -> None:
        self._player.stop()

    def _on_slider_released(self) -> None:
        self._player.setPosition(self._seek_slider.value())
        self._seeking = False

    def _on_position_changed(self, position: int) -> None:
        if not self._seeking:
            self._seek_slider.setValue(position)
        self._position_label.setText(
            f"{_format_ms(position)} / {_format_ms(self._player.duration())}"
        )

    def _on_duration_changed(self, duration: int) -> None:
        self._seek_slider.setRange(0, duration)
