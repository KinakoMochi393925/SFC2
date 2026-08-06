"""変換処理のパラメータを保持するモデル。"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ConversionSettings:
    input_path: str
    output_dir: str
    output_stem: str  # 拡張子なしのファイル名
    output_format: str  # 拡張子相当のフォーマット名（例: "mp4", "av1"）
    category: str  # "video" / "audio" / "image"
    width: Optional[int] = None  # None = オリジナル解像度維持
    height: Optional[int] = None

    # 目標ファイルサイズ指定機能（動画・音声のみ）
    target_size_bytes: Optional[int] = None  # None = 未指定（通常変換）
    priority: Optional[str] = None  # "quality" / "audio"
