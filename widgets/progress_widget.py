"""変換進捗（プログレスバー + パーセンテージ）を表示するウィジェット。"""
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QWidget


class ProgressWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setTextVisible(False)
        self._percent_label = QLabel("0%")
        self._percent_label.setFixedWidth(45)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._bar, stretch=1)
        layout.addWidget(self._percent_label)

    def set_progress(self, value: int) -> None:
        value = max(0, min(100, value))
        self._bar.setValue(value)
        self._percent_label.setText(f"{value}%")

    def reset(self) -> None:
        self.set_progress(0)
