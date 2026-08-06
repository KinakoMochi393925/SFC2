"""SFC2 メインウィンドウ。"""
import os
from pathlib import Path
from typing import Optional

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.conversion_settings import ConversionSettings
from models.file_info import FileInfo
from services.bitrate_calculator import parse_target_size
from services.conversion_worker import ConversionWorker
from services.ffmpeg_locator import find_ffmpeg
from services.media_probe import probe_image, probe_media
from utils.file_type_detector import (
    CATEGORY_AUDIO,
    CATEGORY_IMAGE,
    CATEGORY_VIDEO,
    category_label,
    detect_category,
)
from utils.filename_utils import default_output_stem, sanitize_filename
from utils.format_utils import human_readable_size
from utils.i18n import LanguageManager, tr
from utils.logger import get_logger
from utils.resource_path import resource_path
from widgets.app_settings_dialog import AppSettingsDialog
from widgets.conversion_settings_widget import ConversionSettingsWidget
from widgets.ffmpeg_settings_dialog import FfmpegSettingsDialog
from widgets.output_settings_widget import OutputSettingsWidget
from widgets.preview_area import PreviewArea
from widgets.progress_widget import ProgressWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(780, 780)
        self.setWindowIcon(QIcon(resource_path("resources/favicon.ico")))

        self._file_info: Optional[FileInfo] = None
        self._worker: Optional[ConversionWorker] = None
        self._current_file_size_bytes: int = 0
        self._current_source_size = (None, None)

        self._build_ui()
        self._build_menu()

        LanguageManager.instance().language_changed.connect(self._retranslate_ui)
        self._retranslate_ui()

    # ------------------------------------------------------------------
    # UI構築
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        self._file_label = QLabel()
        self._file_label.setStyleSheet("font-weight: bold;")
        self._meta_label = QLabel("")
        self._meta_label.setStyleSheet("color: #888888;")
        self._category_label = QLabel("")
        self._category_label.setStyleSheet("color: #666666;")

        info_layout = QHBoxLayout()
        info_layout.addWidget(self._file_label, stretch=1)
        info_layout.addWidget(self._meta_label)
        info_layout.addWidget(self._category_label)
        root.addLayout(info_layout)

        # ファイル選択（D&D/クリック）とプレビュー表示を兼ねるエリア
        self._preview_area = PreviewArea()
        self._preview_area.file_selected.connect(self._on_file_selected)
        root.addWidget(self._preview_area, stretch=1)

        self._conversion_settings = ConversionSettingsWidget()
        self._conversion_settings.settings_changed.connect(self._on_settings_changed)
        root.addWidget(self._conversion_settings)

        self._output_settings = OutputSettingsWidget()
        root.addWidget(self._output_settings)

        self._convert_button = QPushButton()
        self._convert_button.setObjectName("primaryButton")
        self._convert_button.setEnabled(False)
        self._convert_button.clicked.connect(self._on_convert_clicked)
        root.addWidget(self._convert_button)

        self._progress_widget = ProgressWidget()
        root.addWidget(self._progress_widget)

        self._status_label = QLabel("")
        self._status_label.setWordWrap(True)
        root.addWidget(self._status_label)

    def _build_menu(self) -> None:
        self._settings_menu = self.menuBar().addMenu("")
        self._app_settings_action = self._settings_menu.addAction("")
        self._app_settings_action.triggered.connect(self._open_app_settings)

    # ------------------------------------------------------------------
    # ファイル選択
    # ------------------------------------------------------------------
    def _on_file_selected(self, path: str) -> None:
        if not Path(path).is_file():
            self._show_error(tr("error_load_failed"))
            return

        category = detect_category(path)
        if category is None:
            self._show_error(tr("error_unsupported_format"))
            self._reset_selection()
            return

        self._file_info = FileInfo(path=path, category=category)
        self._file_label.setText(self._file_info.name)
        self._category_label.setText(category_label(category))

        source_width, source_height = self._probe_source_dimensions(category, path)
        self._current_file_size_bytes = Path(path).stat().st_size
        self._current_source_size = (source_width, source_height)
        self._meta_label.setText(self._format_meta_text(source_width, source_height, self._current_file_size_bytes))

        self._conversion_settings.set_category(category, source_width, source_height)
        self._output_settings.set_output_dir(self._file_info.directory)
        self._output_settings.set_filename_stem(default_output_stem(path))
        self._output_settings.set_extension(self._conversion_settings.selected_format())

        self._progress_widget.reset()
        self._status_label.setText("")
        self._convert_button.setEnabled(True)

        self._load_preview(category, path)

    @staticmethod
    def _format_meta_text(width: Optional[int], height: Optional[int], size_bytes: int) -> str:
        size_text = human_readable_size(size_bytes)
        if width and height:
            return f"{width}×{height} ・ {size_text}"
        return size_text

    def _probe_source_dimensions(self, category: str, path: str):
        """アスペクト比固定機能のため、元ファイルの解像度を取得する（失敗しても無視する）。"""
        try:
            if category == CATEGORY_IMAGE:
                info = probe_image(path)
                return info.width, info.height
            if category == CATEGORY_VIDEO:
                ffmpeg_path = find_ffmpeg()
                if ffmpeg_path:
                    info = probe_media(ffmpeg_path, path)
                    return info.width, info.height
        except Exception:
            get_logger().exception("解像度の取得に失敗")
        return None, None

    def _on_settings_changed(self) -> None:
        if self._file_info is not None:
            self._output_settings.set_extension(self._conversion_settings.selected_format())

    def _load_preview(self, category: str, path: str) -> None:
        try:
            if category == CATEGORY_VIDEO:
                from widgets.video_preview import VideoPreviewWidget

                widget = VideoPreviewWidget()
                widget.load(path)
            elif category == CATEGORY_AUDIO:
                from widgets.audio_preview import AudioPreviewWidget

                widget = AudioPreviewWidget()
                widget.load(path)
            else:  # CATEGORY_IMAGE
                from widgets.image_preview import ImagePreviewWidget

                widget = ImagePreviewWidget()
                widget.load(path)
        except Exception as e:
            get_logger().exception("プレビュー読み込みに失敗")
            self._show_error(tr("error_load_failed") + f" ({e})")
            self._reset_selection()
            return

        self._preview_area.set_preview_widget(widget)

    def _reset_selection(self) -> None:
        """未選択状態に戻す。"""
        self._file_info = None
        self._file_label.setText(tr("no_file_selected"))
        self._meta_label.setText("")
        self._category_label.setText("")
        self._convert_button.setEnabled(False)
        self._preview_area.show_placeholder()

    # ------------------------------------------------------------------
    # 変換処理
    # ------------------------------------------------------------------
    def _on_convert_clicked(self) -> None:
        if self._file_info is None:
            return

        output_dir = self._output_settings.output_dir()
        if not output_dir or not Path(output_dir).is_dir():
            self._show_error(tr("error_output_dir_missing"))
            return

        if not os.access(output_dir, os.W_OK):
            self._show_error(tr("error_output_dir_no_permission"))
            return

        raw_stem = self._output_settings.filename_stem()
        stem = sanitize_filename(raw_stem)
        if not stem:
            self._show_error(tr("error_invalid_filename"))
            return

        target_size_text = self._conversion_settings.target_size_text()
        target_size_bytes = None
        if target_size_text:
            target_size_bytes = parse_target_size(target_size_text)
            if target_size_bytes is None:
                self._show_error(tr("error_invalid_target_size"))
                return
            # 現在のファイルサイズ以上を指定した場合は無視する（縮小にならないため）
            if target_size_bytes >= self._current_file_size_bytes:
                target_size_bytes = None

        ffmpeg_path = find_ffmpeg()
        if ffmpeg_path is None:
            QMessageBox.warning(self, tr("ffmpeg_not_found_title"), tr("ffmpeg_not_found_message"))
            dialog = FfmpegSettingsDialog(self)
            if dialog.exec():
                ffmpeg_path = find_ffmpeg()
            if ffmpeg_path is None:
                self._show_error(tr("error_ffmpeg_unavailable"))
                return

        width, height = self._conversion_settings.selected_resolution()
        settings = ConversionSettings(
            input_path=self._file_info.path,
            output_dir=output_dir,
            output_stem=stem,
            output_format=self._conversion_settings.selected_format(),
            category=self._file_info.category,
            width=width,
            height=height,
            target_size_bytes=target_size_bytes,
            priority=self._conversion_settings.selected_priority(),
        )

        self._start_conversion(ffmpeg_path, settings)

    def _start_conversion(self, ffmpeg_path: str, settings: ConversionSettings) -> None:
        self._convert_button.setEnabled(False)
        self._progress_widget.reset()
        self._status_label.setText(tr("converting_status"))

        self._worker = ConversionWorker(ffmpeg_path, settings)
        self._worker.progress_changed.connect(self._progress_widget.set_progress)
        self._worker.finished_signal.connect(self._on_conversion_finished)
        self._worker.size_warning.connect(self._on_size_warning)
        self._worker.start()

    def _on_size_warning(self, size_mb: str) -> None:
        self._convert_button.setEnabled(True)
        self._status_label.setText("")
        QMessageBox.warning(self, tr("size_warning_title"), tr("size_warning_message", size=size_mb))

    def _on_conversion_finished(self, success: bool, output_path: str, error_message: str) -> None:
        self._convert_button.setEnabled(True)

        if success:
            self._progress_widget.set_progress(100)
            self._status_label.setText(tr("conversion_complete_status", path=output_path))
            QMessageBox.information(
                self, tr("conversion_complete_title"), tr("conversion_complete_message", path=output_path)
            )
        elif error_message:
            self._status_label.setText(tr("conversion_failed_status"))
            get_logger().error("Conversion failed: %s", error_message)
            self._show_error(tr("conversion_failed_message", error=error_message))

        self._worker = None

    # ------------------------------------------------------------------
    # 設定
    # ------------------------------------------------------------------
    def _open_app_settings(self) -> None:
        dialog = AppSettingsDialog(self)
        dialog.exec()

    # ------------------------------------------------------------------
    # 共通ヘルパー
    # ------------------------------------------------------------------
    def _show_error(self, message: str) -> None:
        get_logger().error(message)
        QMessageBox.critical(self, tr("error_title"), message)

    def _retranslate_ui(self, _lang=None) -> None:
        self.setWindowTitle(tr("app_title"))
        if self._file_info is None:
            self._file_label.setText(tr("no_file_selected"))
        else:
            self._category_label.setText(category_label(self._file_info.category))
        self._convert_button.setText(tr("convert_button"))
        self._settings_menu.setTitle(tr("menu_settings"))
        self._app_settings_action.setText(tr("menu_app_settings"))

    def closeEvent(self, event) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait(2000)
        super().closeEvent(event)
