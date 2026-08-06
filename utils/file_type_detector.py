"""拡張子からファイル種別 (video / audio / image) を判定する。"""
from pathlib import Path
from typing import Optional

from utils.constants import AUDIO_EXTENSIONS, IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
from utils.i18n import tr

CATEGORY_VIDEO = "video"
CATEGORY_AUDIO = "audio"
CATEGORY_IMAGE = "image"

_CATEGORY_LABEL_KEYS = {
    CATEGORY_VIDEO: "category_video",
    CATEGORY_AUDIO: "category_audio",
    CATEGORY_IMAGE: "category_image",
}


def detect_category(file_path: str) -> Optional[str]:
    """ファイルパスから種別を判定する。未対応拡張子の場合は None を返す。"""
    ext = Path(file_path).suffix.lower()
    if ext in VIDEO_EXTENSIONS:
        return CATEGORY_VIDEO
    if ext in AUDIO_EXTENSIONS:
        return CATEGORY_AUDIO
    if ext in IMAGE_EXTENSIONS:
        return CATEGORY_IMAGE
    return None


def category_label(category: Optional[str]) -> str:
    key = _CATEGORY_LABEL_KEYS.get(category)
    return tr(key) if key else tr("category_unknown")
