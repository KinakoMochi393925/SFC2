"""SFC2 エントリポイント。起動速度を優先し、必要最小限のモジュールのみをここで読み込む。"""
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from ui.style import STYLE_SHEET
from utils.logger import install_excepthook
from utils.resource_path import resource_path


def main() -> int:
    install_excepthook()

    app = QApplication(sys.argv)
    app.setApplicationName("SFC2")
    app.setStyleSheet(STYLE_SHEET)
    app.setWindowIcon(QIcon(resource_path("resources/favicon.ico")))

    # メインウィンドウの読み込みはここで行う（重いプレビュー/FFmpeg関連は
    # ウィジェット側で実際に使うタイミングまで遅延初期化される）
    from ui.main_window import MainWindow

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
