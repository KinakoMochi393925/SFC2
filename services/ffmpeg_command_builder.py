"""FFmpeg コマンドライン引数の組み立て。

フォーマットごとのコーデック/コンテナのマッピングと、GIF用パレット変換、
目標ファイルサイズ指定時の2パスエンコードにも対応する。
"""
from pathlib import Path
from typing import List, Optional

from models.conversion_settings import ConversionSettings
from services.bitrate_calculator import BitratePlan

# 動画ソースから音声のみを抜き出す（映像を除去する）フォーマット
AUDIO_ONLY_FORMATS = {"wav", "mp3", "m4a", "ogg", "flac"}

# カバーアート（埋め込みサムネイル画像）の保持に対応している音声フォーマット
AUDIO_COVER_ART_FORMATS = {"mp3", "m4a", "flac"}

# フォーマット名 -> (出力拡張子, 映像コーデック, 音声コーデック, GIFかどうか)
# 2パスエンコード時は1回目(-f null)と2回目で同じコーデックを使う必要があるため、
# すべてのコンテナに対して明示的にコーデックを指定する
# （指定しないと -f null 使用時にFFmpegのデフォルトコーデック選択が
#   本来の出力と食い違い、2回目のパスで統計ファイルを読めなくなる）。
FORMAT_INFO = {
    "mp4": {"ext": "mp4", "video_codec": "libx264", "audio_codec": "aac"},
    "avi": {"ext": "avi", "video_codec": "mpeg4", "audio_codec": "libmp3lame"},
    "mov": {"ext": "mov", "video_codec": "libx264", "audio_codec": "aac"},
    "mkv": {"ext": "mkv", "video_codec": "libx264", "audio_codec": "aac"},
    "wmv": {"ext": "wmv", "video_codec": "wmv2", "audio_codec": "wmav2"},
    "webm": {"ext": "webm", "video_codec": "libvpx-vp9", "audio_codec": "libopus"},
    "av1": {"ext": "webm", "video_codec": "libaom-av1", "audio_codec": "libopus"},
    "gif": {"ext": "gif", "is_gif": True},
    "wav": {"ext": "wav"},
    "mp3": {"ext": "mp3"},
    "m4a": {"ext": "m4a"},
    "ogg": {"ext": "ogg"},
    "flac": {"ext": "flac"},
    "jpg": {"ext": "jpg"},
    "jpeg": {"ext": "jpeg"},
    "png": {"ext": "png"},
    "bmp": {"ext": "bmp"},
    "webp": {"ext": "webp"},
}


def get_output_extension(output_format: str) -> str:
    """出力フォーマット名から実際のファイル拡張子を返す（例: "av1" -> "webm"）。"""
    info = FORMAT_INFO.get(output_format.lower())
    return info["ext"] if info else output_format.lower()


def _scale_filter(width: Optional[int], height: Optional[int]) -> Optional[str]:
    if width and height:
        return f"scale={width}:{height}"
    return None


def build_command(
    ffmpeg_path: str,
    output_path: Path,
    settings: ConversionSettings,
    bitrate_plan: Optional[BitratePlan] = None,
    pass_number: Optional[int] = None,
    passlog_prefix: Optional[str] = None,
    null_output: str = "/dev/null",
) -> List[str]:
    """FFmpeg コマンドを組み立てる。

    pass_number が 1 の場合は2パスエンコードの1回目（解析のみ、出力は捨てる）。
    pass_number が 2 の場合は2回目（実際の出力ファイルを書き出す）。
    pass_number が None の場合は通常の1回きりの変換。
    """
    info = FORMAT_INFO.get(settings.output_format.lower(), {})
    cmd: List[str] = [ffmpeg_path, "-y", "-i", settings.input_path]

    if info.get("is_gif"):
        return _build_gif_command(cmd, output_path, settings)

    # 解像度（ビットレートプランで再計算された値があれば優先）
    width = bitrate_plan.width if (bitrate_plan and bitrate_plan.width) else settings.width
    height = bitrate_plan.height if (bitrate_plan and bitrate_plan.height) else settings.height

    is_audio_only_output = (
        settings.category == "video" and settings.output_format.lower() in AUDIO_ONLY_FORMATS
    )

    if settings.category in ("video", "image") and not is_audio_only_output:
        scale = _scale_filter(width, height)
        if scale:
            cmd += ["-vf", scale]
        if bitrate_plan and bitrate_plan.fps:
            cmd += ["-r", str(bitrate_plan.fps)]

    if is_audio_only_output:
        cmd += ["-vn"]
    elif settings.category == "audio":
        out_fmt = settings.output_format.lower()
        if out_fmt in AUDIO_COVER_ART_FORMATS:
            cmd += ["-map", "0:a", "-map", "0:v?", "-c:v", "copy"]
            if out_fmt == "mp3":
                cmd += ["-id3v2_version", "3"]
        else:
            cmd += ["-vn"]
    elif "video_codec" in info:
        cmd += ["-c:v", info["video_codec"]]

    if bitrate_plan and bitrate_plan.video_bitrate_bps and not is_audio_only_output:
        cmd += ["-b:v", str(bitrate_plan.video_bitrate_bps)]

    if settings.category in ("video", "audio"):
        if "audio_codec" in info and not is_audio_only_output:
            cmd += ["-c:a", info["audio_codec"]]
        if bitrate_plan and bitrate_plan.audio_bitrate_bps:
            cmd += ["-b:a", str(bitrate_plan.audio_bitrate_bps)]

    if pass_number is not None:
        cmd += ["-pass", str(pass_number)]
        if passlog_prefix:
            cmd += ["-passlogfile", passlog_prefix]
        if pass_number == 1:
            cmd += ["-an", "-f", "null", null_output]
            return cmd

    cmd += [str(output_path)]
    return cmd


def _build_gif_command(
    cmd: List[str], output_path: Path, settings: ConversionSettings
) -> List[str]:
    """高品質パレットを使ったGIF変換コマンドを組み立てる。"""
    scale = _scale_filter(settings.width, settings.height)
    scale_prefix = f"{scale}," if scale else ""
    filter_chain = (
        f"{scale_prefix}split[s0][s1];[s0]palettegen=max_colors=256[p];[s1][p]paletteuse"
    )
    cmd += ["-vf", filter_chain, "-an", str(output_path)]
    return cmd


def needs_two_pass(settings: ConversionSettings, bitrate_plan: Optional[BitratePlan]) -> bool:
    """2パスエンコードが必要かどうか判定する（動画かつ映像ビットレート指定時のみ）。"""
    if bitrate_plan is None or bitrate_plan.video_bitrate_bps is None:
        return False
    info = FORMAT_INFO.get(settings.output_format.lower(), {})
    if info.get("is_gif"):
        return False
    if settings.category == "video" and settings.output_format.lower() in AUDIO_ONLY_FORMATS:
        return False
    return settings.category == "video"
