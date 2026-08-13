"""ドラッグ＆ドロップ・クリックによるファイル選択と、選択後のプレビュー表示を
同じ領域で行うウィジェット。ファイル未選択時は選択エリアとして、選択後は
プレビューエリアとして機能する。"""
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import QFileDialog, QLabel, QVBoxLayout, QWidget

from utils.i18n import LanguageManager, tr

_EMPTY_STYLE = (
    "#previewArea {"
    "  background-color: #fafafa;"
    "  border: 2px dashed #b0b0b0;"
    "  border-radius: 6px;"
    "}"
    "#previewArea:hover {"
    "  border-color: #808080;"
    "}"
)

_LOADED_STYLE = (
    "#previewArea {"
    "  background-color: #ffffff;"
    "  border: 1px solid #d5d5d5;"
    "  border-radius: 6px;"
    "}"
)


class PreviewArea(QWidget):
    files_selected = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setObjectName("previewArea")
        self.setMinimumHeight(260)
        self.setStyleSheet(_EMPTY_STYLE)

        self._layout = QVBoxLayout(self)
        self._placeholder = QLabel()
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("color: #555555; font-size: 13px; border: none;")
        self._layout.addWidget(self._placeholder)

        self._preview_widget: Optional[QWidget] = None

        LanguageManager.instance().language_changed.connect(self._retranslate_ui)
        self._retranslate_ui()

    # ------------------------------------------------------------------
    def show_placeholder(self) -> None:
        """未選択状態の表示に戻す。"""
        self._clear_preview_widget()
        self._placeholder.setVisible(True)
        self.setStyleSheet(_EMPTY_STYLE)

    def set_preview_widget(self, widget: QWidget) -> None:
        """指定したプレビューウィジェットをこのエリアに表示する。"""
        self._clear_preview_widget()
        self._placeholder.setVisible(False)
        self._layout.addWidget(widget)
        self._preview_widget = widget
        self.setStyleSheet(_LOADED_STYLE)

    def _clear_preview_widget(self) -> None:
        if self._preview_widget is not None:
            self._layout.removeWidget(self._preview_widget)
            self._preview_widget.deleteLater()
            self._preview_widget = None

    # ------------------------------------------------------------------
    # クリックでファイル選択（子ウィジェット＝再生ボタン等が処理しなかった
    # クリックのみここに伝播するため、プレビュー操作の邪魔にならない）
    # ------------------------------------------------------------------
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._open_file_dialog()
        super().mousePressEvent(event)

    def _open_file_dialog(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self)
        if paths:
            self.files_selected.emit(paths)

    def _retranslate_ui(self, _lang=None) -> None:
        self._placeholder.setText(tr("drop_placeholder"))

    # ------------------------------------------------------------------
    # ドラッグ＆ドロップ
    # ------------------------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if not urls:
            return
        paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
        if paths:
            self.files_selected.emit(paths)
