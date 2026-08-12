"""出力フォーマット・解像度・目標ファイルサイズ/優先度を設定するウィジェット。"""
from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import (
    QAbstractSpinBox,
    QButtonGroup,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

from settings.app_settings import (
    get_default_video_format,
    get_default_audio_format,
    get_default_image_format,
)

from utils.constants import (
    AUDIO_OUTPUT_FORMATS,
    CATEGORY_COLORS,
    IMAGE_OUTPUT_FORMATS,
    PRIORITY_AUDIO,
    PRIORITY_QUALITY,
    RESOLUTION_OPTIONS,
    VIDEO_OUTPUT_FORMATS,
)
from utils.file_type_detector import CATEGORY_AUDIO, CATEGORY_IMAGE, CATEGORY_VIDEO
from utils.i18n import LanguageManager, tr

_FORMATS_BY_CATEGORY = {
    CATEGORY_VIDEO: VIDEO_OUTPUT_FORMATS,
    CATEGORY_AUDIO: AUDIO_OUTPUT_FORMATS,
    CATEGORY_IMAGE: IMAGE_OUTPUT_FORMATS,
}

_SIZE_UNITS = ["KB", "MB", "GB"]

_LOCK_BUTTON_STYLE = """
QPushButton { background-color: #ffffff; border: 1px solid #c0c0c0; border-radius: 4px; }
QPushButton:hover { background-color: #ececec; }
QPushButton:checked { background-color: #3a7afe; border: 1px solid #2f68e0; color: #ffffff; }
QPushButton:disabled { color: #bbbbbb; background-color: #f5f5f5; }
"""

_TOGGLE_BUTTON_STYLE = """
QPushButton {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    border-radius: 14px;
    padding: 4px 14px;
}
QPushButton:hover { background-color: #ececec; }
QPushButton:checked {
    background-color: #3a7afe;
    border: 1px solid #2f68e0;
    color: #ffffff;
    font-weight: bold;
}
"""


def _resolution_label(resolution_id: str, value) -> str:
    if resolution_id == "original":
        return tr("resolution_original")
    if resolution_id == "custom":
        return tr("resolution_custom")
    return f"{value[0]}×{value[1]}"


def _round_even(value: float) -> int:
    n = int(round(value))
    return n + (n % 2)


class ConversionSettingsWidget(QWidget):
    settings_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("conversionSettingsWidget")

        self._current_category: Optional[str] = None
        self._source_ratio: Optional[float] = None  # 元ファイルの幅/高さ
        self._aspect_locked = False

        # --- フォーマット / 解像度 -------------------------------------------------
        self._format_combo = QComboBox()
        self._resolution_combo = QComboBox()
        for resolution_id, value in RESOLUTION_OPTIONS:
            self._resolution_combo.addItem(_resolution_label(resolution_id, value), resolution_id)

        self._width_spin = self._make_plain_spinbox()
        self._height_spin = self._make_plain_spinbox()

        # アスペクト比固定ボタン（幅・高さの右側に配置。ONのとき青色になる）
        self._lock_button = QPushButton("🔗")
        self._lock_button.setCheckable(True)
        self._lock_button.setFixedWidth(36)
        self._lock_button.setStyleSheet(_LOCK_BUTTON_STYLE)
        self._lock_button.toggled.connect(self._on_lock_toggled)

        custom_layout = QHBoxLayout()
        custom_layout.setContentsMargins(0, 0, 0, 0)
        custom_layout.addWidget(self._width_spin)
        custom_layout.addWidget(self._height_spin)
        custom_layout.addWidget(self._lock_button)
        self._custom_widget = QWidget()
        self._custom_widget.setLayout(custom_layout)
        self._custom_widget.setVisible(False)

        # --- 目標ファイルサイズ（数値のみ + 単位選択） -----------------------------
        self._target_size_value_edit = QLineEdit()
        self._target_size_value_edit.setValidator(QDoubleValidator(0.0, 999999.0, 2, self))
        self._target_size_unit_combo = QComboBox()
        self._target_size_unit_combo.addItems(_SIZE_UNITS)
        self._target_size_unit_combo.setCurrentText("MB")

        target_size_layout = QHBoxLayout()
        target_size_layout.setContentsMargins(0, 0, 0, 0)
        target_size_layout.addWidget(self._target_size_value_edit, stretch=1)
        target_size_layout.addWidget(self._target_size_unit_combo)
        self._target_size_widget = QWidget()
        self._target_size_widget.setLayout(target_size_layout)

        # --- 優先度（チェックボックス風トグルボタン） -------------------------------
        self._priority_quality_button = QPushButton()
        self._priority_audio_button = QPushButton()
        for btn in (self._priority_quality_button, self._priority_audio_button):
            btn.setCheckable(True)
            btn.setStyleSheet(_TOGGLE_BUTTON_STYLE)
        self._priority_quality_button.setChecked(True)

        self._priority_group = QButtonGroup(self)
        self._priority_group.setExclusive(True)
        self._priority_group.addButton(self._priority_quality_button)
        self._priority_group.addButton(self._priority_audio_button)

        priority_layout = QHBoxLayout()
        priority_layout.setContentsMargins(0, 0, 0, 0)
        priority_layout.addWidget(self._priority_quality_button)
        priority_layout.addWidget(self._priority_audio_button)
        priority_layout.addStretch(1)
        self._priority_widget = QWidget()
        self._priority_widget.setLayout(priority_layout)

        # --- レイアウト --------------------------------------------------------
        self._form = QFormLayout(self)
        self._format_label = self._add_row(self._format_combo)
        self._resolution_label_widget = self._add_row(self._resolution_combo)
        self._custom_size_label_widget = self._add_row(self._custom_widget)
        self._target_size_label_widget = self._add_row(self._target_size_widget)
        self._priority_label_widget = self._add_row(self._priority_widget)

        self._resolution_combo.currentIndexChanged.connect(self._on_resolution_changed)
        self._format_combo.currentTextChanged.connect(self._on_format_changed)
        self._width_spin.valueChanged.connect(self._on_width_changed)
        self._height_spin.valueChanged.connect(self._on_height_changed)
        self._target_size_value_edit.textChanged.connect(self._on_target_size_text_changed)
        self._target_size_unit_combo.currentTextChanged.connect(lambda _: self.settings_changed.emit())
        self._priority_quality_button.toggled.connect(lambda _: self.settings_changed.emit())

        LanguageManager.instance().language_changed.connect(self._retranslate_ui)
        self._retranslate_ui()

    # ------------------------------------------------------------------
    def _add_row(self, widget: QWidget):
        label_widget = QLabel("")
        self._form.addRow(label_widget, widget)
        return label_widget

    @staticmethod
    def _make_plain_spinbox() -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(1, 10000)
        spin.setValue(1920)
        # クリックで1ずつ増減させるボタンは不要という要件のため非表示にする
        spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        spin.wheelEvent = lambda event: None  # ホイールでの誤操作も防止
        return spin

    # ------------------------------------------------------------------
    # カテゴリ / フォーマット
    # ------------------------------------------------------------------
    def set_category(
        self, category: Optional[str], source_width: Optional[int] = None, source_height: Optional[int] = None
    ) -> None:
        """カテゴリに応じて選べるフォーマット・表示項目・アクセントカラーを切り替える。"""
        self._current_category = category

        self._format_combo.blockSignals(True)
        self._format_combo.clear()
        
        formats = _FORMATS_BY_CATEGORY.get(category, [])
        self._format_combo.addItems(formats)
        
        # Apply default format if set
        default_format = None
        if category == CATEGORY_VIDEO:
            default_format = get_default_video_format()
        elif category == CATEGORY_AUDIO:
            default_format = get_default_audio_format()
        elif category == CATEGORY_IMAGE:
            default_format = get_default_image_format()
            
        if default_format and default_format in formats:
            self._format_combo.setCurrentText(default_format)

        self._format_combo.blockSignals(False)

        if source_width and source_height:
            self._source_ratio = source_width / source_height
        else:
            self._source_ratio = None
        self._update_lock_button_state()

        resolution_enabled = category in (CATEGORY_VIDEO, CATEGORY_IMAGE)
        self._resolution_combo.setEnabled(resolution_enabled)
        if not resolution_enabled:
            self._resolution_combo.setCurrentIndex(0)
            self._custom_widget.setVisible(False)

        self._apply_category_color(category)
        self._update_target_size_visibility()
        self._on_format_changed(self._format_combo.currentText())

    def _apply_category_color(self, category: Optional[str]) -> None:
        """ジャンル（カテゴリ）別のアクセントカラーをパネル全体の背景に適用する。"""
        color = CATEGORY_COLORS.get(category)
        if color is None:
            self.setStyleSheet("")
            return
        r, g, b = color
        self.setStyleSheet(
            f"#conversionSettingsWidget {{"
            f" background-color: rgb({r},{g},{b});"
            f" border-radius: 6px;"
            f" padding: 6px;"
            f" }}"
        )

    def _on_format_changed(self, _text: str) -> None:
        self._update_target_size_visibility()
        self.settings_changed.emit()

    def _on_target_size_text_changed(self, _text: str) -> None:
        self._update_target_size_visibility()
        self.settings_changed.emit()

    def _update_target_size_visibility(self) -> None:
        is_gif = self._format_combo.currentText().lower() == "gif"
        size_applicable = self._current_category in (CATEGORY_VIDEO, CATEGORY_AUDIO) and not is_gif
        self._target_size_label_widget.setVisible(size_applicable)
        self._target_size_widget.setVisible(size_applicable)

        has_value = bool(self._target_size_value_edit.text().strip())
        priority_visible = size_applicable and has_value
        self._priority_label_widget.setVisible(priority_visible)
        self._priority_widget.setVisible(priority_visible)

    # ------------------------------------------------------------------
    # 解像度 / アスペクト比固定
    # ------------------------------------------------------------------
    def _on_resolution_changed(self, _index: int) -> None:
        resolution_id = self._resolution_combo.currentData()
        self._custom_widget.setVisible(resolution_id == "custom")
        self.settings_changed.emit()

    def _update_lock_button_state(self) -> None:
        available = self._source_ratio is not None
        self._lock_button.setEnabled(available)
        if not available:
            self._lock_button.setChecked(False)
            self._lock_button.setToolTip(tr("aspect_lock_unavailable"))

    def _on_lock_toggled(self, checked: bool) -> None:
        self._aspect_locked = checked
        self._lock_button.setToolTip(
            tr("aspect_lock_tooltip_on") if checked else tr("aspect_lock_tooltip_off")
        )
        if checked and self._source_ratio:
            # ロックした瞬間に高さを幅に合わせて再計算する
            new_height = _round_even(self._width_spin.value() / self._source_ratio)
            self._height_spin.blockSignals(True)
            self._height_spin.setValue(max(self._height_spin.minimum(), new_height))
            self._height_spin.blockSignals(False)

    def _on_width_changed(self, value: int) -> None:
        if self._aspect_locked and self._source_ratio:
            new_height = _round_even(value / self._source_ratio)
            self._height_spin.blockSignals(True)
            self._height_spin.setValue(max(self._height_spin.minimum(), min(self._height_spin.maximum(), new_height)))
            self._height_spin.blockSignals(False)
        self.settings_changed.emit()

    def _on_height_changed(self, value: int) -> None:
        if self._aspect_locked and self._source_ratio:
            new_width = _round_even(value * self._source_ratio)
            self._width_spin.blockSignals(True)
            self._width_spin.setValue(max(self._width_spin.minimum(), min(self._width_spin.maximum(), new_width)))
            self._width_spin.blockSignals(False)
        self.settings_changed.emit()

    # ------------------------------------------------------------------
    # 値の取得
    # ------------------------------------------------------------------
    def selected_format(self) -> str:
        return self._format_combo.currentText()

    def selected_resolution(self) -> tuple[Optional[int], Optional[int]]:
        """(width, height) を返す。オリジナル維持の場合は (None, None)。"""
        resolution_id = self._resolution_combo.currentData()
        if resolution_id == "original" or resolution_id is None:
            return None, None
        if resolution_id == "custom":
            return self._width_spin.value(), self._height_spin.value()
        for rid, value in RESOLUTION_OPTIONS:
            if rid == resolution_id:
                return value
        return None, None

    def target_size_text(self) -> str:
        """"10MB" のような文字列を返す（未入力時は空文字列）。"""
        if not self._target_size_widget.isVisible():
            return ""
        value = self._target_size_value_edit.text().strip()
        if not value:
            return ""
        return f"{value}{self._target_size_unit_combo.currentText()}"

    def selected_priority(self) -> str:
        return PRIORITY_AUDIO if self._priority_audio_button.isChecked() else PRIORITY_QUALITY

    # ------------------------------------------------------------------
    # 多言語対応
    # ------------------------------------------------------------------
    def _retranslate_ui(self, _lang: Optional[str] = None) -> None:
        self._format_label.setText(tr("output_format_label"))
        self._resolution_label_widget.setText(tr("resolution_label"))
        self._custom_size_label_widget.setText(tr("custom_size_label"))
        self._target_size_label_widget.setText(tr("target_size_label"))
        self._priority_label_widget.setText(tr("priority_label"))
        self._target_size_value_edit.setPlaceholderText(tr("target_size_placeholder"))
        self._priority_quality_button.setText(tr("priority_quality"))
        self._priority_audio_button.setText(tr("priority_audio"))

        current_data = self._resolution_combo.currentData()
        self._resolution_combo.blockSignals(True)
        self._resolution_combo.clear()
        for resolution_id, value in RESOLUTION_OPTIONS:
            self._resolution_combo.addItem(_resolution_label(resolution_id, value), resolution_id)
        if current_data is not None:
            index = self._resolution_combo.findData(current_data)
            if index >= 0:
                self._resolution_combo.setCurrentIndex(index)
        self._resolution_combo.blockSignals(False)

        self._update_lock_button_state()
        if self._lock_button.isEnabled():
            self._lock_button.setToolTip(
                tr("aspect_lock_tooltip_on") if self._aspect_locked else tr("aspect_lock_tooltip_off")
            )
