"""画像プレビュー用ウィジェット。Pillow で読み込み、幅広い形式に対応する。"""
from PIL import Image
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ImagePreviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._original_pixmap: QPixmap | None = None

        self._label = QLabel("画像プレビュー")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setMinimumSize(1, 1)

        layout = QVBoxLayout(self)
        layout.addWidget(self._label)

    def load(self, file_path: str) -> None:
        with Image.open(file_path) as img:
            img = img.convert("RGBA")
            qimage = QImage(
                img.tobytes("raw", "RGBA"),
                img.width,
                img.height,
                QImage.Format.Format_RGBA8888,
            )
            self._original_pixmap = QPixmap.fromImage(qimage.copy())
        self._rescale()

    def clear(self) -> None:
        self._original_pixmap = None
        self._label.clear()
        self._label.setText("画像プレビュー")

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._rescale()

    def _rescale(self) -> None:
        if self._original_pixmap is None:
            return
        scaled = self._original_pixmap.scaled(
            self._label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._label.setPixmap(scaled)
