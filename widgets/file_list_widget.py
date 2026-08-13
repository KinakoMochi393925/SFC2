"""追加されたファイルの一覧を表示し、選択や削除を行うウィジェット。"""
from typing import List, Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDragMoveEvent, QDropEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from models.file_info import FileInfo
from utils.i18n import LanguageManager, tr


class FileListWidget(QWidget):
    selection_changed = pyqtSignal(str)  # 選択されたファイルのパスを通知
    files_deleted = pyqtSignal(list)     # 削除されたパスのリストを通知
    list_cleared = pyqtSignal()          # リストがクリアされたことを通知
    files_dropped = pyqtSignal(list)     # ドロップされたファイルのパスのリストを通知

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(200)
        self.setMaximumWidth(350)
        
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        
        self._title_label = QLabel()
        self._title_label.setStyleSheet("font-weight: bold; color: #222222;")
        self._layout.addWidget(self._title_label)
        
        self._list_widget = QListWidget()
        self._list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self._list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.setAcceptDrops(True)
        self._layout.addWidget(self._list_widget)
        
        self._button_layout = QHBoxLayout()
        self._delete_button = QPushButton()
        self._delete_button.setEnabled(False)
        self._delete_button.clicked.connect(self._on_delete_clicked)
        self._clear_button = QPushButton()
        self._clear_button.setEnabled(False)
        self._clear_button.clicked.connect(self._on_clear_clicked)
        
        self._button_layout.addWidget(self._delete_button)
        self._button_layout.addWidget(self._clear_button)
        self._layout.addLayout(self._button_layout)
        
        LanguageManager.instance().language_changed.connect(self._retranslate_ui)
        self._retranslate_ui()

    def add_file(self, file_info: FileInfo) -> None:
        """ファイルをリストに追加する。既に存在する場合は無視する。"""
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            if item is not None:
                info = item.data(Qt.ItemDataRole.UserRole)
                if info and isinstance(info, FileInfo) and info.path == file_info.path:
                    return
                
        item = QListWidgetItem(file_info.name)
        item.setData(Qt.ItemDataRole.UserRole, file_info)
        item.setToolTip(file_info.path)
        self._list_widget.addItem(item)
        self._update_buttons()

    def select_file(self, path: str) -> None:
        """指定したパスのファイルを選択状態にする。"""
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            if item is not None:
                info = item.data(Qt.ItemDataRole.UserRole)
                if info and isinstance(info, FileInfo) and info.path == path:
                    self._list_widget.setCurrentItem(item)
                    break

    def get_all_files(self) -> List[FileInfo]:
        """リスト上の全ての FileInfo を返す。"""
        files = []
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            if item is not None:
                info = item.data(Qt.ItemDataRole.UserRole)
                if info and isinstance(info, FileInfo):
                    files.append(info)
        return files

    def get_selected_file(self) -> Optional[FileInfo]:
        """現在選択されている FileInfo を返す。"""
        selected_items = self._list_widget.selectedItems()
        if selected_items:
            info = selected_items[0].data(Qt.ItemDataRole.UserRole)
            if isinstance(info, FileInfo):
                return info
        return None

    def _on_selection_changed(self) -> None:
        self._update_buttons()
        selected = self.get_selected_file()
        if selected:
            self.selection_changed.emit(selected.path)

    def _on_delete_clicked(self) -> None:
        selected_items = self._list_widget.selectedItems()
        if not selected_items:
            return
            
        deleted_paths = []
        self._list_widget.blockSignals(True)
        try:
            for item in selected_items:
                info = item.data(Qt.ItemDataRole.UserRole)
                if info and isinstance(info, FileInfo):
                    deleted_paths.append(info.path)
                row = self._list_widget.row(item)
                removed_item = self._list_widget.takeItem(row)
                del removed_item
        finally:
            self._list_widget.blockSignals(False)
            
        self._update_buttons()
        self.files_deleted.emit(deleted_paths)

    def _on_clear_clicked(self) -> None:
        self._list_widget.blockSignals(True)
        try:
            self._list_widget.clear()
        finally:
            self._list_widget.blockSignals(False)
            
        self._update_buttons()
        self.list_cleared.emit()

    def _update_buttons(self) -> None:
        has_items = self._list_widget.count() > 0
        has_selection = len(self._list_widget.selectedItems()) > 0
        self._clear_button.setEnabled(has_items)
        self._delete_button.setEnabled(has_selection)

    def _retranslate_ui(self, _lang=None) -> None:
        self._title_label.setText(tr("list_title"))
        self._delete_button.setText(tr("list_delete"))
        self._clear_button.setText(tr("list_clear_all"))

    def dragEnterEvent(self, a0: QDragEnterEvent) -> None:
        mime_data = a0.mimeData()
        if mime_data and mime_data.hasUrls():
            a0.acceptProposedAction()

    def dragMoveEvent(self, a0: QDragMoveEvent) -> None:
        mime_data = a0.mimeData()
        if mime_data and mime_data.hasUrls():
            a0.acceptProposedAction()

    def dropEvent(self, a0: QDropEvent) -> None:
        mime_data = a0.mimeData()
        if mime_data:
            urls = mime_data.urls()
            if urls:
                paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
                if paths:
                    self.files_dropped.emit(paths)