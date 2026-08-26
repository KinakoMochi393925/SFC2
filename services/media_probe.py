"""入力ファイルの解像度・再生時間を取得する。

FFmpeg を同梱しない方針のため ffprobe には依存せず、`ffmpeg -i <file>` を
出力ファイル指定なしで実行し、標準エラー出力に表示されるメタ情報
（Duration / Video: ... WxH ...）を解析して取得する。
"""
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional

from PIL import Image

_DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")
_DIMENSION_RE = re.compile(r"Video:.*?(\d{2,5})x(\d{2,5})")


@dataclass
class MediaInfo:
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None


def probe_image(path: str) -> MediaInfo:
    """Pillow で画像の解像度を取得する。"""
    with Image.open(path) as img:
        return MediaInfo(duration_seconds=None, width=img.width, height=img.height)


def probe_media(ffmpeg_path: str, path: str) -> MediaInfo:
    """FFmpeg のメタ情報表示（stderr）から動画の解像度・再生時間を取得する。"""
    cmd = [ffmpeg_path, "-hide_banner", "-i", path]
    popen_kwargs = dict(
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        encoding="utf-8",
        errors="replace",
    )
    if sys.platform == "win32":
        popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    try:
        process = subprocess.Popen(cmd, **popen_kwargs)
        _, stderr_text = process.communicate(timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return MediaInfo()

    info = MediaInfo()
    duration_match = _DURATION_RE.search(stderr_text)
    if duration_match:
        h, m, s = duration_match.groups()
        info.duration_seconds = int(h) * 3600 + int(m) * 60 + float(s)

    dimension_match = _DIMENSION_RE.search(stderr_text)
    if dimension_match:
        info.width = int(dimension_match.group(1))
        info.height = int(dimension_match.group(2))

    return info


def extract_audio_thumbnail(ffmpeg_path: str, path: str) -> Optional[bytes]:
    """音声ファイルに埋め込まれているカバーアート/サムネイル画像を抽出してPNGバイナリとして返す。

    画像が存在しない場合や抽出に失敗した場合は None を返す。
    """
    cmd = [
        ffmpeg_path,
        "-hide_banner",
        "-i",
        path,
        "-an",
        "-vframes",
        "1",
        "-c:v",
        "png",
        "-f",
        "image2pipe",
        "-",
    ]
    popen_kwargs = dict(
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if sys.platform == "win32":
        popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    try:
        process = subprocess.Popen(cmd, **popen_kwargs)
        stdout_data, _ = process.communicate(timeout=10)
        if process.returncode == 0 and stdout_data:
            return stdout_data
    except (OSError, subprocess.TimeoutExpired):
        return None

    return None

