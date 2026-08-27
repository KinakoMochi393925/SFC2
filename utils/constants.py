"""アプリ全体で使う定数・パス定義。"""
from pathlib import Path

# プロジェクトルート（main.py が置かれているディレクトリ）
BASE_DIR = Path(__file__).resolve().parent.parent

LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "app.log"

APP_NAME = "SFC2"
ORG_NAME = "SFC2"

# OS (Windows / Mac / Linux) で共通して使用を避けるべきファイル名文字
# （Windowsの禁止文字に加え、Mac/Linuxのパス区切りや予約文字を網羅）
INVALID_FILENAME_CHARS = '\\/:*?"<>|'

# カテゴリごとの拡張子
VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v", ".mpg", ".mpeg"}
AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".flac", ".wma"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif", ".tiff"}

# 変換先として選べる形式（カテゴリ別）
# "av1" は webm コンテナに AV1 コーデックを使用する
VIDEO_OUTPUT_FORMATS = ["mp4", "avi", "mov", "mkv", "wmv", "webm", "av1", "gif", "wav", "mp3"]
AUDIO_OUTPUT_FORMATS = ["wav", "mp3", "m4a", "ogg", "flac"]
IMAGE_OUTPUT_FORMATS = ["jpg", "jpeg", "png", "bmp", "webp"]

# ジャンル（カテゴリ）別のアクセントカラー (R, G, B)
CATEGORY_COLORS = {
    "video": (188, 226, 232),
    "image": (249, 210, 215),
    "audio": (165, 212, 173),
}

# 解像度プリセット: (内部ID, 表示ラベル or 翻訳キー, 値)
# 値: None=オリジナル維持 / (width, height) / "custom"=カスタム入力
RESOLUTION_OPTIONS = [
    ("original", None),
    ("1920x1080", (1920, 1080)),
    ("1280x720", (1280, 720)),
    ("854x480", (854, 480)),
    ("1080x1920", (1080, 1920)),
    ("custom", "custom"),
]

# UI言語
LANGUAGE_JA = "ja"
LANGUAGE_EN = "en"
DEFAULT_LANGUAGE = LANGUAGE_JA

# 目標ファイルサイズ指定時の優先度
PRIORITY_QUALITY = "quality"  # 画質優先（音声ビットレートを削る）
PRIORITY_AUDIO = "audio"  # 音声優先（映像ビットレート/解像度/fpsを削る）

# コーデック別の BPP (Bits Per Pixel Frame) 安全しきい値
# 圧縮効率の高いコーデックは低い BPP でも高画質を維持可能
CODEC_BPP_SAFE_MAP = {
    "libaom-av1": 0.030,
    "libvpx-vp9": 0.040,
    "libx264": 0.050,
    "mpeg4": 0.075,
    "wmv2": 0.075,
}
DEFAULT_BPP_SAFE_MIN = 0.05
DEFAULT_BPP_CRITICAL_MIN = 0.025

# 段階的に下げるfps・解像度短辺/長辺基準
FPS_STEPS = [60, 30, 24]
TARGET_SHORT_SIDES = [1080, 720, 480, 360]

# 画質優先/音声優先の音声ビットレート範囲 (bps)
AUDIO_BITRATE_QUALITY_PRIORITY = (48_000, 64_000)
AUDIO_BITRATE_AUDIO_PRIORITY = (128_000, 192_000)
AUDIO_BITRATE_MIN_FALLBACK = 32_000  # 超低ビットレート時の音声最低保証

