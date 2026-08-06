"""FFmpeg 実行ファイルのパスを表示・変更する部品（ダイアログ間で共通利用）。"""
from PyQt6.QtWidgets import QFileDialog, QHBoxLayout, QLineEdit, QPushButton, QWidget

from settings.app_settings import get_custom_ffmpeg_path, set_custom_ffmpeg_path
from utils.i18n import LanguageManager, tr


class FfmpegPathWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._path_edit = QLineEdit(get_custom_ffmpeg_path() or "")
        self._browse_button = QPushButton()
        self._browse_button.clicked.connect(self._browse)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._path_edit)
        layout.addWidget(self._browse_button)

        LanguageManager.instance().language_changed.connect(self._retranslate_ui)
        self._retranslate_ui()

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, tr("ffmpeg_settings_title"), filter="ffmpeg.exe;;All Files (*)")
        if path:
            self._path_edit.setText(path)

    def save(self) -> None:
        set_custom_ffmpeg_path(self._path_edit.text().strip())

    def _retranslate_ui(self, _lang=None) -> None:
        self._browse_button.setText(tr("browse_button"))
