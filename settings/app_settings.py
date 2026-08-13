"""QSettings を使ったアプリ設定の永続化。FFmpeg のユーザー指定パスや UI言語などを保存する。"""
from typing import Optional

from PyQt6.QtCore import QSettings

from utils.constants import APP_NAME, DEFAULT_LANGUAGE, ORG_NAME

_KEY_FFMPEG_PATH = "ffmpeg/custom_path"
_KEY_LANGUAGE = "ui/language"
_KEY_OPEN_FILE = "post_conversion/open_file"
_KEY_OPEN_FOLDER = "post_conversion/open_folder"

_KEY_DEFAULT_VIDEO_FORMAT = "default_formats/video"
_KEY_DEFAULT_AUDIO_FORMAT = "default_formats/audio"
_KEY_DEFAULT_IMAGE_FORMAT = "default_formats/image"

_KEY_INCLUDE_SUBFOLDERS = "post_conversion/include_subfolders"



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


def get_open_file_after() -> bool:
    # QSettings returns str ('true'/'false') on some platforms if saved dynamically,
    # but type=bool handles it safely. We can default to False.
    return _settings().value(_KEY_OPEN_FILE, False, type=bool)


def set_open_file_after(value: bool) -> None:
    _settings().setValue(_KEY_OPEN_FILE, value)


def get_open_folder_after() -> bool:
    return _settings().value(_KEY_OPEN_FOLDER, False, type=bool)


def set_open_folder_after(value: bool) -> None:
    _settings().setValue(_KEY_OPEN_FOLDER, value)


def get_default_video_format() -> Optional[str]:
    value = _settings().value(_KEY_DEFAULT_VIDEO_FORMAT, "", type=str)
    return value or None


def set_default_video_format(format_str: str) -> None:
    _settings().setValue(_KEY_DEFAULT_VIDEO_FORMAT, format_str)


def get_default_audio_format() -> Optional[str]:
    value = _settings().value(_KEY_DEFAULT_AUDIO_FORMAT, "", type=str)
    return value or None


def set_default_audio_format(format_str: str) -> None:
    _settings().setValue(_KEY_DEFAULT_AUDIO_FORMAT, format_str)


def get_default_image_format() -> Optional[str]:
    value = _settings().value(_KEY_DEFAULT_IMAGE_FORMAT, "", type=str)
    return value or None


def set_default_image_format(format_str: str) -> None:
    _settings().setValue(_KEY_DEFAULT_IMAGE_FORMAT, format_str)


def get_include_subfolders() -> bool:
    return _settings().value(_KEY_INCLUDE_SUBFOLDERS, False, type=bool)


def set_include_subfolders(value: bool) -> None:
    _settings().setValue(_KEY_INCLUDE_SUBFOLDERS, value)
