"""SFC2 メインウィンドウ。"""
import os
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices, QIcon
from PyQt6.QtWidgets import (
    QFileDialog,
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
from services.media_probe import MediaInfo, MediaProbeWorker, probe_image, probe_media
from settings.app_settings import (
    get_open_file_after,
    get_open_folder_after,
    get_include_subfolders,
    get_default_video_format,
    get_default_audio_format,
    get_default_image_format,
)
from utils.constants import AUDIO_OUTPUT_FORMATS, IMAGE_OUTPUT_FORMATS, VIDEO_OUTPUT_FORMATS
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
from widgets.file_list_widget import FileListWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(780, 780)
        self.setWindowIcon(QIcon(resource_path("resources/favicon.ico")))

        self._file_info: Optional[FileInfo] = None
        self._worker: Optional[ConversionWorker] = None
        self._probe_workers: list[MediaProbeWorker] = []
        self._current_file_size_bytes: int = 0
        self._current_source_size = (None, None)
        self._conversion_queue: list[ConversionSettings] = []
        self._current_conversion_total: int = 0
        self._current_conversion_index: int = 0
        self._failed_conversions: list[tuple[str, str]] = []
        self._current_conversion_settings: Optional[ConversionSettings] = None

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
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        self._file_list = FileListWidget()
        self._file_list.selection_changed.connect(self._on_list_selection_changed)
        self._file_list.files_deleted.connect(self._on_files_deleted)
        self._file_list.list_cleared.connect(self._on_list_cleared)
        self._file_list.files_dropped.connect(self._on_files_dropped)
        self._file_list.add_file_requested.connect(self._on_add_file_requested)
        self._file_list.add_folder_requested.connect(self._on_add_folder_requested)
        main_layout.addWidget(self._file_list)

        right_panel = QWidget()
        root = QVBoxLayout(right_panel)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(12)
        main_layout.addWidget(right_panel, stretch=1)

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
        self._preview_area.files_selected.connect(self._on_files_dropped)
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
    def _on_files_dropped(self, paths: list[str]) -> None:
        include_subfolders = get_include_subfolders()
        added_any = False
        for path_str in paths:
            path = Path(path_str)
            if path.is_file():
                if self._add_single_file(path_str, base_dir=str(path.parent)):
                    added_any = True
            elif path.is_dir():
                if self._add_folder(path, base_dir=str(path), include_subfolders=include_subfolders):
                    added_any = True

        if added_any:
            self._file_list.select_last()
        self._convert_button.setEnabled(len(self._file_list.get_all_files()) > 0)

    def _on_add_file_requested(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self)
        if paths:
            self._on_files_dropped(paths)

    def _on_add_folder_requested(self) -> None:
        folder = QFileDialog.getExistingDirectory(self)
        if folder:
            self._on_files_dropped([folder])

    def _add_folder(self, folder_path: Path, base_dir: str, include_subfolders: bool) -> bool:
        """フォルダ内のファイルをリストに追加する。1件以上追加したらTrueを返す。"""
        added_any = False
        try:
            if include_subfolders:
                for root, _, files in os.walk(folder_path):
                    for f in files:
                        if self._add_single_file(os.path.join(root, f), base_dir=base_dir):
                            added_any = True
            else:
                for child in folder_path.iterdir():
                    if child.is_file():
                        if self._add_single_file(str(child), base_dir=base_dir):
                            added_any = True
        except OSError as e:
            self._show_error(tr("error_file_operation", error=str(e)))
        return added_any

    def _add_single_file(self, path_str: str, base_dir: str) -> bool:
        """単一ファイルをリストに追加する。追加したらTrueを返す。"""
        category = detect_category(path_str)
        if category is not None:
            file_info = FileInfo(path=path_str, category=category, base_dir=base_dir)
            return self._file_list.add_file(file_info)
        return False

    def _on_list_selection_changed(self, path: str) -> None:
        category = detect_category(path)
        if category is None:
            return

        selected_file = self._file_list.get_selected_file()
        if not selected_file:
            return

        try:
            file_size = Path(path).stat().st_size
        except OSError as e:
            self._show_error(tr("error_file_operation", error=str(e)))
            self._reset_selection()
            return

        self._file_info = selected_file
        self._file_label.setText(self._file_info.name)
        self._category_label.setText(category_label(category))

        self._current_file_size_bytes = file_size
        self._current_source_size = (None, None)
        self._meta_label.setText(self._format_meta_text(None, None, file_size))

        self._conversion_settings.set_category(category, None, None)
        # Use existing output_dir or file's directory if first time
        current_output_dir = self._output_settings.output_dir()
        if not current_output_dir:
            self._output_settings.set_output_dir(self._file_info.directory)
            
        self._output_settings.set_filename_stem(default_output_stem(path))
        self._output_settings.set_extension(self._conversion_settings.selected_format())

        self._progress_widget.reset()
        self._status_label.setText("")

        self._load_preview(category, path)
        self._start_source_probe(category, path)

    def _on_files_deleted(self, deleted_paths: list[str]) -> None:
        remaining = self._file_list.get_all_files()
        if not remaining:
            # リストが空になったら情報をクリア
            self._reset_selection()
            self._reset_output_settings()
            self._convert_button.setEnabled(False)
        elif self._file_info and self._file_info.path in deleted_paths:
            # 選択中のファイルが削除された場合は選択をリセット（リストは残る）
            self._reset_selection()
            self._convert_button.setEnabled(True)
        else:
            self._convert_button.setEnabled(True)

    def _on_list_cleared(self) -> None:
        self._reset_selection()
        self._reset_output_settings()
        self._convert_button.setEnabled(False)

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

    def _start_source_probe(self, category: str, path: str) -> None:
        ffmpeg_path = find_ffmpeg() if category == CATEGORY_VIDEO else None
        worker = MediaProbeWorker(category, path, ffmpeg_path, self)
        worker.completed.connect(self._on_source_probe_completed)
        worker.finished.connect(self._on_source_probe_finished)
        worker.finished.connect(worker.deleteLater)
        self._probe_workers.append(worker)
        worker.start()

    def _on_source_probe_completed(self, path: str, info: MediaInfo) -> None:
        if self._file_info is None or self._file_info.path != path:
            return

        self._current_source_size = (info.width, info.height)
        self._meta_label.setText(
            self._format_meta_text(info.width, info.height, self._current_file_size_bytes)
        )
        self._conversion_settings.set_category(
            self._file_info.category, info.width, info.height
        )

    def _on_source_probe_finished(self) -> None:
        worker = self.sender()
        if isinstance(worker, MediaProbeWorker) and worker in self._probe_workers:
            self._probe_workers.remove(worker)

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

    def _reset_output_settings(self) -> None:
        """変換対象が空になったとき、次の追加ファイルから保存先を決め直せるようにする。"""
        self._output_settings.set_output_dir("")
        self._output_settings.set_filename_stem("")
        self._output_settings.set_extension("")

    # ------------------------------------------------------------------
    # 変換処理
    # ------------------------------------------------------------------
    def _on_convert_clicked(self) -> None:
        files = self._file_list.get_all_files()
        if not files:
            return

        output_dir_base = self._output_settings.output_dir()
        if not output_dir_base or not Path(output_dir_base).is_dir():
            self._show_error(tr("error_output_dir_missing"))
            return

        if not os.access(output_dir_base, os.W_OK):
            self._show_error(tr("error_output_dir_no_permission"))
            return

        categories = set(f.category for f in files if f.category is not None)
        default_formats = {
            CATEGORY_VIDEO: get_default_video_format(),
            CATEGORY_AUDIO: get_default_audio_format(),
            CATEGORY_IMAGE: get_default_image_format(),
        }

        if len(categories) > 1:
            missing = []
            for cat in categories:
                if not default_formats[cat]:
                    missing.append(category_label(cat))
            if missing:
                missing_str = "\n".join(f"- {m}" for m in missing)
                self._show_error(tr("error_default_format_missing", missing_types=missing_str))
                return

        ffmpeg_path = find_ffmpeg()
        if ffmpeg_path is None:
            QMessageBox.warning(self, tr("ffmpeg_not_found_title"), tr("ffmpeg_not_found_message"))
            dialog = FfmpegSettingsDialog(self)
            if dialog.exec():
                ffmpeg_path = find_ffmpeg()
            if ffmpeg_path is None:
                self._show_error(tr("error_ffmpeg_unavailable"))
                return

        self._conversion_queue.clear()
        target_size_text = self._conversion_settings.target_size_text()
        target_size_bytes_global = parse_target_size(target_size_text) if target_size_text else None
        width, height = self._conversion_settings.selected_resolution()
        priority = self._conversion_settings.selected_priority()

        for f in files:
            cat = f.category
            if cat is None:
                continue

            if len(categories) == 1:
                # 単一カテゴリ：現在UIで選択されているフォーマットがそのカテゴリに属するか確認
                ui_format = self._conversion_settings.selected_format()
                formats_for_cat = {
                    CATEGORY_VIDEO: VIDEO_OUTPUT_FORMATS,
                    CATEGORY_AUDIO: AUDIO_OUTPUT_FORMATS,
                    CATEGORY_IMAGE: IMAGE_OUTPUT_FORMATS,
                }.get(cat, [])
                if ui_format in formats_for_cat:
                    out_format = ui_format
                else:
                    # UIのフォーマットがこのカテゴリ向けでない場合（ありえないはずだが保険）
                    out_format = default_formats.get(cat) or ui_format
            else:
                out_format = default_formats[cat]

            if f.base_dir:
                try:
                    rel_path = Path(f.path).parent.relative_to(Path(f.base_dir))
                    out_dir = Path(output_dir_base) / rel_path
                except ValueError:
                    out_dir = Path(output_dir_base)
            else:
                out_dir = Path(output_dir_base)

            try:
                out_dir.mkdir(parents=True, exist_ok=True)
                file_size = Path(f.path).stat().st_size
            except OSError as e:
                self._show_error(tr("error_file_operation", error=str(e)))
                return

            target_size = target_size_bytes_global
            if target_size and target_size >= file_size:
                target_size = None

            stem = sanitize_filename(default_output_stem(f.path))
            if not stem:
                continue

            settings = ConversionSettings(
                input_path=f.path,
                output_dir=str(out_dir),
                output_stem=stem,
                output_format=out_format,
                category=cat,
                width=width,
                height=height,
                target_size_bytes=target_size,
                priority=priority,
            )
            self._conversion_queue.append((ffmpeg_path, settings))

        if not self._conversion_queue:
            return

        self._current_conversion_total = len(self._conversion_queue)
        self._current_conversion_index = 0
        self._failed_conversions.clear()
        self._convert_button.setEnabled(False)
        self._start_next_conversion()

    def _start_next_conversion(self) -> None:
        if getattr(self, '_worker', None) is not None:
            self._worker.wait()
            self._worker.deleteLater()
            self._worker = None

        if not self._conversion_queue:
            self._convert_button.setEnabled(True)
            self._progress_widget.set_progress(100)
            
            if self._failed_conversions:
                self._status_label.setText(tr("batch_conversion_complete_with_errors"))
                error_lines = "\n".join(f"- {name}: {err}" for name, err in self._failed_conversions)
                QMessageBox.warning(
                    self, 
                    tr("conversion_complete_with_errors_title"), 
                    tr("conversion_complete_with_errors_message", errors=error_lines)
                )
            else:
                self._status_label.setText(tr("batch_conversion_complete_status"))
                msg = tr("batch_conversion_complete_message") if self._current_conversion_total > 1 else tr("conversion_complete_message", path=getattr(self, '_last_success_path', ''))
                QMessageBox.information(
                    self, tr("conversion_complete_title"), msg
                )
            
            if get_open_folder_after():
                output_dir = self._output_settings.output_dir()
                if output_dir:
                    QDesktopServices.openUrl(QUrl.fromLocalFile(output_dir))
                    
            self._worker = None
            return

        ffmpeg_path, settings = self._conversion_queue.pop(0)
        self._current_conversion_settings = settings
        self._current_conversion_index += 1
        
        self._progress_widget.reset()
        if self._current_conversion_total > 1:
            status = tr("batch_converting_status", current=self._current_conversion_index, total=self._current_conversion_total)
        else:
            status = tr("converting_status")
        self._status_label.setText(status)

        self._worker = ConversionWorker(ffmpeg_path, settings)
        self._worker.progress_changed.connect(self._progress_widget.set_progress)
        self._worker.finished_signal.connect(self._on_conversion_finished)
        self._worker.size_warning.connect(self._on_size_warning)
        self._worker.start()

    def _on_size_warning(self, size_mb: str) -> None:
        if self._current_conversion_settings:
            filename = Path(self._current_conversion_settings.input_path).name
            self._failed_conversions.append((filename, tr("size_warning_message", size=size_mb)))
        self._start_next_conversion()

    def _on_conversion_finished(self, success: bool, output_path: str, error_message: str) -> None:
        if success:
            self._last_success_path = output_path
            if self._current_conversion_total == 1 and get_open_file_after():
                QDesktopServices.openUrl(QUrl.fromLocalFile(output_path))
        else:
            if self._current_conversion_settings:
                filename = Path(self._current_conversion_settings.input_path).name
                self._failed_conversions.append((filename, error_message or tr("conversion_failed_status")))
                get_logger().error("Conversion failed for %s: %s", filename, error_message)
        
        self._start_next_conversion()

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
            self._worker.stop()
            self._worker.wait()

        for probe_worker in self._probe_workers:
            if probe_worker.isRunning():
                probe_worker.wait()

        super().closeEvent(event)
