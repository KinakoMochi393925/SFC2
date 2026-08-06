"""出力ファイル名のサニタイズと重複回避（自動採番）。"""
from pathlib import Path

from utils.constants import INVALID_FILENAME_CHARS


def sanitize_filename(name: str) -> str:
    """Windows で使用禁止の文字を除去する。前後の空白・ドットも除去する。"""
    cleaned = "".join(ch for ch in name if ch not in INVALID_FILENAME_CHARS)
    cleaned = cleaned.strip().strip(".")
    return cleaned


def default_output_stem(input_path: str) -> str:
    """入力ファイル名から `元ファイル名_cnv` の形式のデフォルト出力名（拡張子なし）を作る。"""
    stem = Path(input_path).stem
    return sanitize_filename(f"{stem}_cnv") or "output_cnv"


def generate_unique_output_path(directory: str, stem: str, extension: str) -> Path:
    """同名ファイルが存在する場合、name(1).ext, name(2).ext ... のように自動採番する。"""
    ext = extension.lower().lstrip(".")
    dir_path = Path(directory)
    candidate = dir_path / f"{stem}.{ext}"
    if not candidate.exists():
        return candidate

    counter = 1
    while True:
        candidate = dir_path / f"{stem}({counter}).{ext}"
        if not candidate.exists():
            return candidate
        counter += 1
