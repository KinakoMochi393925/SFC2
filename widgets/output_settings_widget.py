"""保存先フォルダと出力ファイル名を設定するウィジェット。"""
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QWidget,
)

from utils.i18n import LanguageManager, tr


class OutputSettingsWidget(QWidget):
    filename_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._dir_edit = QLineEdit()
        self._browse_button = QPushButton()
        self._browse_button.clicked.connect(self._browse_dir)

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self._dir_edit)
        dir_layout.addWidget(self._browse_button)

        self._filename_edit = QLineEdit()
        self._filename_edit.textEdited.connect(self.filename_changed)
        self._extension_field = QLineEdit()
        self._extension_field.setReadOnly(True)
        self._extension_field.setFixedWidth(70)
        self._extension_field.setStyleSheet("background-color: #f0f0f0;")

        filename_layout = QHBoxLayout()
        filename_layout.addWidget(self._filename_edit, stretch=1)
        filename_layout.addWidget(self._extension_field)

        self._form = QFormLayout(self)
        self._dir_label = self._add_row(dir_layout)
        self._filename_label = self._add_row(filename_layout)

        LanguageManager.instance().language_changed.connect(self._retranslate_ui)
        self._retranslate_ui()

    def _add_row(self, layout):
        from PyQt6.QtWidgets import QLabel

        label = QLabel("")
        self._form.addRow(label, layout)
        return label

    def _browse_dir(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, tr("output_dir_label"), self._dir_edit.text())
        if directory:
            self._dir_edit.setText(directory)

    def set_output_dir(self, directory: str) -> None:
        self._dir_edit.setText(directory)

    def output_dir(self) -> str:
        return self._dir_edit.text().strip()

    def set_filename_stem(self, stem: str) -> None:
        self._filename_edit.setText(stem)

    def filename_stem(self) -> str:
        return self._filename_edit.text().strip()

    def set_extension(self, extension: str) -> None:
        self._extension_field.setText(f".{extension}" if extension else "")

    def _retranslate_ui(self, _lang=None) -> None:
        self._dir_label.setText(tr("output_dir_label"))
        self._filename_label.setText(tr("output_filename_label"))
        self._browse_button.setText(tr("browse_button"))
