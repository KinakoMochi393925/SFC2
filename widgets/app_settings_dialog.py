"""メニューから開く、アプリ全体の設定ダイアログ（FFmpegパス・UI言語）。"""
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QRadioButton,
    QVBoxLayout,
    QComboBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
    QMessageBox,
)

from settings.app_settings import (
    get_open_file_after,
    get_open_folder_after,
    set_open_file_after,
    set_open_folder_after,
    get_default_video_format,
    set_default_video_format,
    get_default_audio_format,
    set_default_audio_format,
    get_default_image_format,
    set_default_image_format,
    get_include_subfolders,
    set_include_subfolders,
)
from utils.constants import LANGUAGE_EN, LANGUAGE_JA, VIDEO_OUTPUT_FORMATS, AUDIO_OUTPUT_FORMATS, IMAGE_OUTPUT_FORMATS
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
        self._include_subfolders_check = QCheckBox()
        self._include_subfolders_check.setChecked(get_include_subfolders())
        post_conversion_layout.addWidget(self._open_file_check)
        post_conversion_layout.addWidget(self._open_folder_check)
        post_conversion_layout.addWidget(self._include_subfolders_check)

        self._default_format_group = QGroupBox()
        default_format_layout = QFormLayout(self._default_format_group)
        
        self._video_format_combo = QComboBox()
        self._video_format_combo.addItem(tr("default_format_not_set"), "")
        for fmt in VIDEO_OUTPUT_FORMATS:
            self._video_format_combo.addItem(fmt, fmt)
        current_video = get_default_video_format()
        if current_video:
            index = self._video_format_combo.findData(current_video)
            if index >= 0:
                self._video_format_combo.setCurrentIndex(index)
                
        self._audio_format_combo = QComboBox()
        self._audio_format_combo.addItem(tr("default_format_not_set"), "")
        for fmt in AUDIO_OUTPUT_FORMATS:
            self._audio_format_combo.addItem(fmt, fmt)
        current_audio = get_default_audio_format()
        if current_audio:
            index = self._audio_format_combo.findData(current_audio)
            if index >= 0:
                self._audio_format_combo.setCurrentIndex(index)
                
        self._image_format_combo = QComboBox()
        self._image_format_combo.addItem(tr("default_format_not_set"), "")
        for fmt in IMAGE_OUTPUT_FORMATS:
            self._image_format_combo.addItem(fmt, fmt)
        current_image = get_default_image_format()
        if current_image:
            index = self._image_format_combo.findData(current_image)
            if index >= 0:
                self._image_format_combo.setCurrentIndex(index)

        self._video_format_label = QLabel()
        self._audio_format_label = QLabel()
        self._image_format_label = QLabel()
        
        default_format_layout.addRow(self._video_format_label, self._video_format_combo)
        default_format_layout.addRow(self._audio_format_label, self._audio_format_combo)
        default_format_layout.addRow(self._image_format_label, self._image_format_combo)

        import os
        if os.name == "nt":
            self._context_menu_group = QGroupBox()
            context_menu_layout = QHBoxLayout(self._context_menu_group)
            self._register_context_menu_btn = QPushButton()
            self._unregister_context_menu_btn = QPushButton()
            context_menu_layout.addWidget(self._register_context_menu_btn)
            context_menu_layout.addWidget(self._unregister_context_menu_btn)
            
            self._register_context_menu_btn.clicked.connect(self._on_register_context_menu)
            self._unregister_context_menu_btn.clicked.connect(self._on_unregister_context_menu)

        self._buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self._buttons.accepted.connect(self._on_accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self._ffmpeg_group)
        layout.addWidget(self._language_group)
        layout.addWidget(self._default_format_group)
        layout.addWidget(self._post_conversion_group)
        if os.name == "nt":
            layout.addWidget(self._context_menu_group)
        layout.addWidget(self._buttons)

        LanguageManager.instance().language_changed.connect(self._retranslate_ui)
        self._retranslate_ui()

    def _on_register_context_menu(self) -> None:
        from services.windows_context_menu import register_context_menu
        try:
            register_context_menu()
            QMessageBox.information(self, tr("app_settings_title"), tr("context_menu_registered"))
        except Exception:
            QMessageBox.critical(self, tr("error_title"), tr("context_menu_error"))

    def _on_unregister_context_menu(self) -> None:
        from services.windows_context_menu import unregister_context_menu
        try:
            unregister_context_menu()
            QMessageBox.information(self, tr("app_settings_title"), tr("context_menu_unregistered"))
        except Exception:
            QMessageBox.critical(self, tr("error_title"), tr("context_menu_error"))

    def _on_language_toggled(self, checked: bool) -> None:
        if not checked:
            return
        language = LANGUAGE_EN if self._en_radio.isChecked() else LANGUAGE_JA
        LanguageManager.instance().set_language(language)

    def _on_accept(self) -> None:
        self._path_widget.save()
        set_open_file_after(self._open_file_check.isChecked())
        set_open_folder_after(self._open_folder_check.isChecked())
        set_include_subfolders(self._include_subfolders_check.isChecked())
        set_default_video_format(self._video_format_combo.currentData())
        set_default_audio_format(self._audio_format_combo.currentData())
        set_default_image_format(self._image_format_combo.currentData())
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
        self._include_subfolders_check.setText(tr("include_subfolders"))
        
        import os
        if os.name == "nt":
            self._context_menu_group.setTitle(tr("context_menu_group"))
            self._register_context_menu_btn.setText(tr("register_context_menu"))
            self._unregister_context_menu_btn.setText(tr("unregister_context_menu"))
        
        self._default_format_group.setTitle(tr("default_format_group"))
        self._video_format_label.setText(tr("default_video_format"))
        self._audio_format_label.setText(tr("default_audio_format"))
        self._image_format_label.setText(tr("default_image_format"))
        
        self._video_format_combo.setItemText(0, tr("default_format_not_set"))
        self._audio_format_combo.setItemText(0, tr("default_format_not_set"))
        self._image_format_combo.setItemText(0, tr("default_format_not_set"))
