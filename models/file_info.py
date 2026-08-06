"""選択された入力ファイルの情報を保持するモデル。"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class FileInfo:
    path: str
    category: Optional[str]  # "video" / "audio" / "image" / None(未対応)

    @property
    def extension(self) -> str:
        return Path(self.path).suffix.lower().lstrip(".")

    @property
    def name(self) -> str:
        return Path(self.path).name

    @property
    def directory(self) -> str:
        return str(Path(self.path).parent)
