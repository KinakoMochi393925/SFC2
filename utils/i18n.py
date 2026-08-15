"""UIの多言語対応（日本語 / 英語）。

- `tr(key, **kwargs)` で現在の言語の文字列を取得する（{name}形式の埋め込みに対応）。
- 言語切替は `LanguageManager` の `language_changed` シグナルで各ウィジェットへ通知し、
  アプリ再起動なしにその場でUIテキストを切り替える。
"""
from PyQt6.QtCore import QObject, pyqtSignal

from settings.app_settings import get_language, set_language
from utils.constants import LANGUAGE_EN, LANGUAGE_JA

TRANSLATIONS = {
    "app_title": {"ja": "SFC2 - メディア変換", "en": "SFC2 - Media Converter"},
    "no_file_selected": {"ja": "ファイルが選択されていません", "en": "No file selected"},
    "drop_placeholder": {
        "ja": "ここにファイルをドラッグ＆ドロップ\nまたはクリックして選択",
        "en": "Drag & drop a file here\nor click to select",
    },
    "menu_settings": {"ja": "設定", "en": "Settings"},
    "menu_app_settings": {"ja": "アプリの設定...", "en": "App Settings..."},
    "convert_button": {"ja": "変換開始", "en": "Start Conversion"},
    "converting_status": {"ja": "変換中...", "en": "Converting..."},

    # 変換設定
    "output_format_label": {"ja": "変換先フォーマット:", "en": "Output Format:"},
    "resolution_label": {"ja": "解像度:", "en": "Resolution:"},
    "custom_size_label": {"ja": "幅 × 高さ:", "en": "Width × Height:"},
    "resolution_original": {"ja": "オリジナル保持", "en": "Keep Original"},
    "resolution_custom": {"ja": "カスタム", "en": "Custom"},
    "aspect_lock_tooltip_on": {
        "ja": "アスペクト比固定: ON（元ファイルの比率を維持します）",
        "en": "Aspect ratio lock: ON (keeps the source ratio)",
    },
    "aspect_lock_tooltip_off": {"ja": "アスペクト比固定: OFF", "en": "Aspect ratio lock: OFF"},
    "aspect_lock_unavailable": {
        "ja": "元ファイルのアスペクト比を取得できませんでした",
        "en": "Could not read the source aspect ratio",
    },

    # 目標サイズ・優先度
    "target_size_label": {"ja": "目標ファイルサイズ:", "en": "Target File Size:"},
    "target_size_placeholder": {"ja": "例: 10（空欄なら未指定）", "en": "e.g. 10 (leave blank to disable)"},
    "priority_label": {"ja": "優先度:", "en": "Priority:"},
    "priority_quality": {"ja": "画質優先", "en": "Video Quality Priority"},
    "priority_audio": {"ja": "音声優先", "en": "Audio Quality Priority"},

    # 出力設定
    "output_dir_label": {"ja": "保存先フォルダ:", "en": "Output Folder:"},
    "output_filename_label": {"ja": "出力ファイル名:", "en": "Output Filename:"},
    "browse_button": {"ja": "参照...", "en": "Browse..."},

    # カテゴリ表示
    "category_video": {"ja": "動画 (Video)", "en": "Video"},
    "category_audio": {"ja": "音声 (Audio)", "en": "Audio"},
    "category_image": {"ja": "画像 (Image)", "en": "Image"},
    "category_unknown": {"ja": "不明", "en": "Unknown"},

    # FFmpeg設定
    "ffmpeg_settings_title": {"ja": "FFmpeg の設定", "en": "FFmpeg Settings"},
    "ffmpeg_settings_info": {
        "ja": "FFmpeg が見つかりませんでした。\nffmpeg.exe の場所を指定してください。",
        "en": "FFmpeg was not found.\nPlease specify the location of ffmpeg.exe.",
    },
    "ffmpeg_path_group": {"ja": "FFmpegの保存場所", "en": "FFmpeg Location"},
    "language_group": {"ja": "UI言語", "en": "UI Language"},
    "language_ja": {"ja": "日本語", "en": "Japanese"},
    "language_en": {"ja": "英語", "en": "English"},
    "app_settings_title": {"ja": "アプリの設定", "en": "App Settings"},
    "post_conversion_group": {"ja": "変換後の動作", "en": "Post-Conversion Actions"},
    "open_file_after": {"ja": "変換したファイルをデフォルトのアプリで開く", "en": "Open converted file with default app"},
    "open_folder_after": {"ja": "変換後のフォルダを自動で開く", "en": "Open output folder after conversion"},
    "include_subfolders": {"ja": "フォルダ追加時にサブフォルダを含める", "en": "Include subfolders when adding folders"},

    # ファイルリスト
    "list_title": {"ja": "変換対象", "en": "Files to Convert"},
    "list_add_file": {"ja": "ファイルを追加", "en": "Add File"},
    "list_add_folder": {"ja": "フォルダを追加", "en": "Add Folder"},
    "list_delete": {"ja": "削除", "en": "Delete"},
    "list_clear_all": {"ja": "全削除", "en": "Clear All"},


    # 既定の変換先
    "default_format_group": {"ja": "既定の変換先フォーマット", "en": "Default Output Formats"},
    "default_video_format": {"ja": "動画:", "en": "Video:"},
    "default_audio_format": {"ja": "音声:", "en": "Audio:"},
    "default_image_format": {"ja": "画像:", "en": "Image:"},
    "default_format_not_set": {"ja": "（設定しない）", "en": "(Not set)"},

    # エラー・確認メッセージ
    "error_title": {"ja": "エラー", "en": "Error"},
    "error_load_failed": {"ja": "ファイルの読み込みに失敗しました。", "en": "Failed to load the file."},
    "error_unsupported_format": {"ja": "未対応のファイル形式です。", "en": "This file format is not supported."},
    "error_output_dir_missing": {"ja": "保存先フォルダが存在しません。", "en": "The output folder does not exist."},
    "error_output_dir_no_permission": {
        "ja": "保存先フォルダへの書き込み権限がありません。",
        "en": "You do not have write permission for the output folder.",
    },
    "error_invalid_filename": {
        "ja": "出力ファイル名が不正です。使用できない文字が含まれていないか確認してください。",
        "en": "The output filename is invalid. Please check for unsupported characters.",
    },
    "ffmpeg_not_found_title": {"ja": "FFmpegが見つかりません", "en": "FFmpeg Not Found"},
    "ffmpeg_not_found_message": {
        "ja": "FFmpegが見つかりませんでした。保存場所を指定してください。",
        "en": "FFmpeg was not found. Please specify its location.",
    },
    "error_ffmpeg_unavailable": {
        "ja": "FFmpegが見つからないため変換を開始できません。",
        "en": "Cannot start conversion because FFmpeg was not found.",
    },
    "conversion_complete_title": {"ja": "変換完了", "en": "Conversion Complete"},
    "conversion_complete_message": {
        "ja": "変換が完了しました。\n\n{path}",
        "en": "Conversion completed.\n\n{path}",
    },
    "conversion_complete_status": {"ja": "変換が完了しました: {path}", "en": "Conversion completed: {path}"},
    "batch_conversion_complete_status": {"ja": "すべての変換が完了しました", "en": "All conversions completed"},
    "batch_conversion_complete_with_errors": {"ja": "一部のファイルの変換に失敗しました", "en": "Some conversions failed"},
    "batch_converting_status": {"ja": "変換中... ({current}/{total})", "en": "Converting... ({current}/{total})"},
    "conversion_failed_status": {"ja": "変換に失敗しました。", "en": "Conversion failed."},
    "conversion_failed_message": {
        "ja": "変換に失敗しました。\n\n{error}",
        "en": "Conversion failed.\n\n{error}",
    },
    "conversion_complete_with_errors_title": {"ja": "変換完了（一部エラー）", "en": "Conversion Complete (with errors)"},
    "conversion_complete_with_errors_message": {
        "ja": "変換が完了しましたが、以下のファイルはエラーのためスキップされました：\n\n{errors}",
        "en": "Conversion completed, but the following files were skipped due to errors:\n\n{errors}",
    },
    "batch_conversion_complete_message": {
        "ja": "すべてのファイルの変換が完了しました。",
        "en": "All files have been converted successfully.",
    },
    "error_default_format_missing": {
        "ja": "複数の種類のファイルが含まれていますが、以下の種類の既定の変換先が設定されていません。\n\n{missing_types}\n\n設定画面から既定の変換先を設定してください。",
        "en": "Multiple file types are included, but default output formats are not set for the following types:\n\n{missing_types}\n\nPlease set default output formats in the settings.",
    },

    # 無理な圧縮の警告
    "size_warning_title": {"ja": "変換できません", "en": "Cannot Convert"},
    "size_warning_message": {
        "ja": (
            "指定されたサイズ（{size}MB）が動画の長さに対して小さすぎるため、"
            "画質が破綻するレベルまで劣化してしまいます。\n"
            "このため変換を行うことができません。\n"
            "動画をカットするか、目標サイズを大きくしてください。"
        ),
        "en": (
            "The specified size ({size}MB) is too small for the length of this video, "
            "so quality would degrade to an unusable level.\n"
            "Conversion cannot proceed with these settings.\n"
            "Please trim the video or increase the target size."
        ),
    },
    "error_invalid_target_size": {
        "ja": "目標ファイルサイズの指定が正しくありません（例: 10MB）。",
        "en": "The target file size is invalid (e.g. 10MB).",
    },
    "error_disk_space": {"ja": "保存先のディスク容量が不足しています。", "en": "Not enough disk space at the destination."},
    "error_same_as_input": {
        "ja": "入力ファイルと同じ場所には保存できません。",
        "en": "Cannot save to the same location as the input file.",
    },
    "error_probe_failed": {
        "ja": "ファイル情報の取得に失敗しました。ファイルが破損していないか確認してください。",
        "en": "Failed to read file information. Please check that the file is not corrupted.",
    },
    "error_generic_conversion": {"ja": "変換処理に失敗しました。", "en": "The conversion process failed."},
    "error_file_operation": {
        "ja": "ファイル操作に失敗しました: {error}",
        "en": "File operation failed: {error}",
    },
    "error_unexpected": {
        "ja": "予期しないエラーが発生しました: {error}",
        "en": "An unexpected error occurred: {error}",
    },
    "error_ffmpeg_missing": {
        "ja": "FFmpegの実行ファイルが見つかりませんでした。",
        "en": "The FFmpeg executable could not be found.",
    },
}


class LanguageManager(QObject):
    """アプリ全体の現在の言語を保持し、変更をシグナルで通知するシングルトン。"""

    language_changed = pyqtSignal(str)

    _instance = None

    def __init__(self):
        super().__init__()
        self._language = get_language()

    @classmethod
    def instance(cls) -> "LanguageManager":
        if cls._instance is None:
            cls._instance = LanguageManager()
        return cls._instance

    def language(self) -> str:
        return self._language

    def set_language(self, language: str) -> None:
        if language not in (LANGUAGE_JA, LANGUAGE_EN):
            return
        if language == self._language:
            return
        self._language = language
        set_language(language)
        self.language_changed.emit(language)


def tr(key: str, **kwargs) -> str:
    """現在の言語に対応する文字列を返す。`{name}` 形式のプレースホルダーに対応。"""
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key
    lang = LanguageManager.instance().language()
    text = entry.get(lang) or entry.get(LANGUAGE_JA, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text
