"""白 / ライトグレー基調のフラットデザイン用スタイルシート。"""

STYLE_SHEET = """
QWidget {
    background-color: #f5f5f5;
    color: #222222;
    font-size: 13px;
}

QMainWindow {
    background-color: #f5f5f5;
}

QPushButton {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    padding: 6px 14px;
}

QPushButton:hover {
    background-color: #ececec;
}

QPushButton:pressed {
    background-color: #e0e0e0;
}

QPushButton:disabled {
    color: #aaaaaa;
    background-color: #f0f0f0;
}

QPushButton#primaryButton {
    background-color: #3a7afe;
    color: #ffffff;
    border: none;
    font-weight: bold;
    padding: 8px 20px;
}

QPushButton#primaryButton:hover {
    background-color: #2f68e0;
}

QPushButton#primaryButton:disabled {
    background-color: #b7c9f5;
    color: #ffffff;
}

QLineEdit, QComboBox, QSpinBox {
    background-color: #ffffff;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    padding: 4px 6px;
}

QProgressBar {
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    background-color: #ffffff;
    height: 16px;
}

QProgressBar::chunk {
    background-color: #3a7afe;
    border-radius: 3px;
}

QGroupBox {
    border: 1px solid #d5d5d5;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 8px;
    background-color: #ffffff;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
    color: #444444;
}

QMenuBar {
    background-color: #f5f5f5;
}

QSlider::groove:horizontal {
    border: 1px solid #c0c0c0;
    height: 4px;
    background: #e0e0e0;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #3a7afe;
    width: 12px;
    margin: -5px 0;
    border-radius: 6px;
}
"""
