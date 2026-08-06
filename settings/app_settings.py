"""QSettings を使ったアプリ設定の永続化。FFmpeg のユーザー指定パスや UI言語などを保存する。"""
from typing import Optional

from PyQt6.QtCore import QSettings

from utils.constants import APP_NAME, DEFAULT_LANGUAGE, ORG_NAME

_KEY_FFMPEG_PATH = "ffmpeg/custom_path"
_KEY_LANGUAGE = "ui/language"


def _settings() -> QSettings:
    return QSettings(ORG_NAME, APP_NAME)


def get_custom_ffmpeg_path() -> Optional[str]:
    value = _settings().value(_KEY_FFMPEG_PATH, "", type=str)
    return value or None


def set_custom_ffmpeg_path(path: str) -> None:
    _settings().setValue(_KEY_FFMPEG_PATH, path)


def get_language() -> str:
    return _settings().value(_KEY_LANGUAGE, DEFAULT_LANGUAGE, type=str) or DEFAULT_LANGUAGE


def set_language(language: str) -> None:
    _settings().setValue(_KEY_LANGUAGE, language)
