"""メニューから開く、アプリ全体の設定ダイアログ（FFmpegパス・UI言語）。"""
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QRadioButton,
    QVBoxLayout,
)

from settings.app_settings import (
    get_open_file_after,
    get_open_folder_after,
    set_open_file_after,
    set_open_folder_after,
)
from utils.constants import LANGUAGE_EN, LANGUAGE_JA
from utils.i18n import LanguageManager, tr
from widgets.ffmpeg_path_widget import FfmpegPathWidget


class AppSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(420)

        self._ffmpeg_group = QGroupBox()
        ffmpeg_layout = QVBoxLayout(self._ffmpeg_group)
        self._path_widget = FfmpegPathWidget()
        ffmpeg_layout.addWidget(self._path_widget)

        self._language_group = QGroupBox()
        language_layout = QVBoxLayout(self._language_group)
        self._ja_radio = QRadioButton()
        self._en_radio = QRadioButton()
        self._language_button_group = QButtonGroup(self)
        self._language_button_group.addButton(self._ja_radio)
        self._language_button_group.addButton(self._en_radio)
        if LanguageManager.instance().language() == LANGUAGE_EN:
            self._en_radio.setChecked(True)
        else:
            self._ja_radio.setChecked(True)
        language_layout.addWidget(self._ja_radio)
        language_layout.addWidget(self._en_radio)

        self._ja_radio.toggled.connect(self._on_language_toggled)
        self._en_radio.toggled.connect(self._on_language_toggled)

        self._post_conversion_group = QGroupBox()
        post_conversion_layout = QVBoxLayout(self._post_conversion_group)
        self._open_file_check = QCheckBox()
        self._open_file_check.setChecked(get_open_file_after())
        self._open_folder_check = QCheckBox()
        self._open_folder_check.setChecked(get_open_folder_after())
        post_conversion_layout.addWidget(self._open_file_check)
        post_conversion_layout.addWidget(self._open_folder_check)

        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self._buttons.accepted.connect(self._on_accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self._ffmpeg_group)
        layout.addWidget(self._language_group)
        layout.addWidget(self._post_conversion_group)
        layout.addWidget(self._buttons)

        LanguageManager.instance().language_changed.connect(self._retranslate_ui)
        self._retranslate_ui()

    def _on_language_toggled(self, checked: bool) -> None:
        if not checked:
            return
        language = LANGUAGE_EN if self._en_radio.isChecked() else LANGUAGE_JA
        LanguageManager.instance().set_language(language)

    def _on_accept(self) -> None:
        self._path_widget.save()
        set_open_file_after(self._open_file_check.isChecked())
        set_open_folder_after(self._open_folder_check.isChecked())
        self.accept()

    def _retranslate_ui(self, _lang=None) -> None:
        self.setWindowTitle(tr("app_settings_title"))
        self._ffmpeg_group.setTitle(tr("ffmpeg_path_group"))
        self._language_group.setTitle(tr("language_group"))
        self._ja_radio.setText(tr("language_ja"))
        self._en_radio.setText(tr("language_en"))
        self._post_conversion_group.setTitle(tr("post_conversion_group"))
        self._open_file_check.setText(tr("open_file_after"))
        self._open_folder_check.setText(tr("open_folder_after"))
