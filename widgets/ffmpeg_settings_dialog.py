"""FFmpeg が見つからないときに保存場所を指定してもらうダイアログ。"""
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from utils.i18n import LanguageManager, tr
from widgets.ffmpeg_path_widget import FfmpegPathWidget


class FfmpegSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(420)

        self._info_label = QLabel()
        self._path_widget = FfmpegPathWidget()

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._buttons.accepted.connect(self._on_accept)
        self._buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(self._info_label)
        layout.addWidget(self._path_widget)
        layout.addWidget(self._buttons)

        LanguageManager.instance().language_changed.connect(self._retranslate_ui)
        self._retranslate_ui()

    def _on_accept(self) -> None:
        self._path_widget.save()
        self.accept()

    def _retranslate_ui(self, _lang=None) -> None:
        self.setWindowTitle(tr("ffmpeg_settings_title"))
        self._info_label.setText(tr("ffmpeg_settings_info"))
