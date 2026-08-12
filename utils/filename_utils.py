"""出力ファイル名のサニタイズと重複回避（自動採番）。"""
import re
from pathlib import Path

from utils.constants import INVALID_FILENAME_CHARS


def _remove_control_characters(name: str) -> str:
    """
    Mac/Linux (POSIX) および共通環境向けの制御文字・NULLバイト除去ヘルパー関数。
    \0 (NULL) やその他の制御文字(0x00-0x1F, 0x7F)をファイル名から弾く。
    """
    return re.sub(r'[\x00-\x1f\x7f]', '', name)


def _avoid_windows_reserved_names(name: str) -> str:
    """
    Windows向けの予約名（CON, PRN, AUX, NUL, COM1-9, LPT1-9など）回避ヘルパー関数。
    予約名と一致する場合は、ファイル名の先頭にアンダースコアを付けて無効化する。
    """
    if not name:
        return name
        
    # Windowsでは拡張子を取り除いた部分が予約名と一致するだけで無効になる場合がある（例: CON.txt）
    stem = Path(name).stem.upper()
    reserved = {"CON", "PRN", "AUX", "NUL"}
    reserved.update(f"COM{i}" for i in range(1, 10))
    reserved.update(f"LPT{i}" for i in range(1, 10))
    
    if stem in reserved:
        return f"_{name}"
    return name


def sanitize_filename(name: str) -> str:
    """
    Windows、Mac、Linux の各OSで使用禁止・問題となる文字や名前を除去・置換し、
    安全なファイル名にするクロスプラットフォーム対応のサニタイズ処理。
    既存の挙動（禁止文字や前後の空白・ドットの除去）はそのまま維持。
    """
    # 1. NULLバイトや制御文字の除去 (Linux/Mac等)
    cleaned = _remove_control_characters(name)
    
    # 2. パス区切り文字やOSごとの禁止文字 (\ / : * ? " < > |) を除去
    # (Macのコロン(:)やスラッシュ(/)、Linuxのスラッシュ(/)もここで弾かれる)
    cleaned = "".join(ch for ch in cleaned if ch not in INVALID_FILENAME_CHARS)
    
    # 3. 前後の空白やドットの除去 (Windows等で末尾のドットやスペースが許されない問題への対応)
    cleaned = cleaned.strip().strip(".")
    
    # 4. Windowsの予約ファイル名（CON, PRNなど）を回避
    cleaned = _avoid_windows_reserved_names(cleaned)
    
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
