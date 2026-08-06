"""表示用の簡易フォーマットユーティリティ。"""


def human_readable_size(num_bytes: float) -> str:
    """バイト数を人間が読みやすい単位（B/KB/MB/GB）の文字列に変換する。"""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            if unit == "B":
                return f"{int(size)}{unit}"
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}GB"
