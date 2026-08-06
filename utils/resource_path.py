"""PyInstallerでexe化した場合と通常のPython実行時の両方に対応した、
同梱リソースファイルの絶対パスを取得するユーティリティ。
"""
import sys
from pathlib import Path

from utils.constants import BASE_DIR


def resource_path(relative_path: str) -> str:
    """相対パスから、実行時（開発中 / PyInstallerでexe化後）どちらでも
    正しく参照できる絶対パスを返す。"""
    if hasattr(sys, "_MEIPASS"):
        # PyInstallerでexe化された場合、一時展開フォルダを基準にする
        return str(Path(sys._MEIPASS) / relative_path)
    return str(BASE_DIR / relative_path)