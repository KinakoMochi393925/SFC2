"""FFmpeg 実行ファイルの検索。

優先順位:
  1. システム PATH 環境変数
  2. 設定画面でユーザーが指定したパス

アプリには FFmpeg を同梱しない。起動時ではなく、実際に必要になったタイミング
（初回プレビュー/変換時）にのみ検索する（Lazy Loading）。
"""
import shutil
from pathlib import Path
from typing import Optional

from settings.app_settings import get_custom_ffmpeg_path


def find_ffmpeg() -> Optional[str]:
    """有効な FFmpeg 実行ファイルのパスを返す。見つからない場合は None。"""
    # 1. PATH 環境変数
    path_from_env = shutil.which("ffmpeg")
    if path_from_env:
        return path_from_env

    # 2. ユーザー指定パス（設定画面で保存されたもの）
    custom_path = get_custom_ffmpeg_path()
    if custom_path and Path(custom_path).is_file():
        return custom_path

    # 3. macOS / Linux 標準インストールパスへのフォールバック
    # （GUI アプリ起動時は PATH に Homebrew 等が含まれない場合があるため）
    fallback_paths = [
        "/opt/homebrew/bin/ffmpeg",  # macOS Apple Silicon (Homebrew)
        "/usr/local/bin/ffmpeg",     # macOS Intel (Homebrew) / Linux manual install
        "/opt/local/bin/ffmpeg",     # macOS MacPorts
        "/usr/bin/ffmpeg",           # Linux system package
    ]
    for candidate in fallback_paths:
        if Path(candidate).is_file():
            return candidate

    return None
