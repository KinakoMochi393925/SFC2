"""GUI と CLI で共有する、既存 ``ConversionWorker`` の CLI 用入口。"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from models.conversion_settings import ConversionSettings
from services.ffmpeg_locator import find_ffmpeg
from utils.constants import (
    AUDIO_EXTENSIONS,
    AUDIO_OUTPUT_FORMATS,
    IMAGE_EXTENSIONS,
    IMAGE_OUTPUT_FORMATS,
    VIDEO_EXTENSIONS,
    VIDEO_OUTPUT_FORMATS,
)
from utils.filename_utils import default_output_stem, sanitize_filename
from utils.logger import get_logger


EXIT_SUCCESS = 0
EXIT_DEFAULT_SETTINGS_MISSING = 1
EXIT_PATH_NOT_FOUND = 2
EXIT_FFMPEG_NOT_FOUND = 3
EXIT_CONVERSION_FAILED = 4

CATEGORY_VIDEO = "video"
CATEGORY_AUDIO = "audio"
CATEGORY_IMAGE = "image"

# Keep Qt out of invalid-path CLI calls. The worker class is imported only when
# conversion actually starts; the variable also makes the boundary testable.
ConversionWorker = None


def run_cli_conversion(paths: Iterable[str]) -> int:
    """Convert files/folders without constructing any GUI widgets.

    The conversion itself deliberately remains in :class:`ConversionWorker` so
    FFmpeg invocation, output naming, and error handling are shared with GUI.
    """
    input_paths = [Path(path) for path in paths]
    if not input_paths or any(not path.exists() or not (path.is_file() or path.is_dir()) for path in input_paths):
        return EXIT_PATH_NOT_FOUND

    files = _collect_supported_files(input_paths)
    if not files:
        return EXIT_CONVERSION_FAILED

    formats = _default_formats()
    if any(_invalid_default_format(category, formats.get(category)) for category in {_detect_category(f) for f in files}):
        return EXIT_DEFAULT_SETTINGS_MISSING

    ffmpeg_path = find_ffmpeg()
    if ffmpeg_path is None:
        return EXIT_FFMPEG_NOT_FOUND

    for input_path in files:
        category = _detect_category(input_path)
        assert category is not None
        stem = sanitize_filename(default_output_stem(str(input_path)))
        if not stem:
            return EXIT_CONVERSION_FAILED

        settings = ConversionSettings(
            input_path=str(input_path),
            output_dir=str(input_path.parent),
            output_stem=stem,
            output_format=formats[category],
            category=category,
        )
        get_logger().info("Converting: %s", input_path)
        if not _run_worker(ffmpeg_path, settings):
            get_logger().error("Conversion failed: %s", input_path)
            return EXIT_CONVERSION_FAILED
        get_logger().info("Completed: %s", input_path)

    return EXIT_SUCCESS


def _collect_supported_files(paths: Iterable[Path]) -> list[Path]:
    """Mirror the GUI folder expansion, including its subfolder setting."""
    files: list[Path] = []
    seen: set[Path] = set()
    include_subfolders = _get_include_subfolders()

    for path in paths:
        candidates = [path] if path.is_file() else (
            path.rglob("*") if include_subfolders else path.iterdir()
        )
        for candidate in candidates:
            if candidate.is_file() and _detect_category(candidate) is not None:
                resolved = candidate.resolve()
                if resolved not in seen:
                    seen.add(resolved)
                    files.append(candidate)
    return files


def _default_formats() -> dict[str, Optional[str]]:
    # QSettings (and therefore Qt) is not needed until paths have been checked.
    from settings.app_settings import (
        get_default_audio_format,
        get_default_image_format,
        get_default_video_format,
    )

    return {
        CATEGORY_VIDEO: get_default_video_format(),
        CATEGORY_AUDIO: get_default_audio_format(),
        CATEGORY_IMAGE: get_default_image_format(),
    }


def _get_include_subfolders() -> bool:
    from settings.app_settings import get_include_subfolders
    return get_include_subfolders()


def _invalid_default_format(category: Optional[str], output_format: Optional[str]) -> bool:
    allowed = {
        CATEGORY_VIDEO: VIDEO_OUTPUT_FORMATS,
        CATEGORY_AUDIO: AUDIO_OUTPUT_FORMATS,
        CATEGORY_IMAGE: IMAGE_OUTPUT_FORMATS,
    }.get(category, [])
    return not output_format or output_format.lower() not in allowed


def _run_worker(ffmpeg_path: str, settings: ConversionSettings) -> bool:
    """Run the GUI worker synchronously while retaining its conversion logic."""
    import sys
    result: dict[str, bool] = {"success": False}
    global ConversionWorker
    if ConversionWorker is None:
        from services.conversion_worker import ConversionWorker as worker_class
        ConversionWorker = worker_class
    worker = ConversionWorker(ffmpeg_path, settings)
    worker.finished_signal.connect(lambda success, _output, _error: result.__setitem__("success", success))
    worker.size_warning.connect(lambda _size: result.__setitem__("success", False))

    def on_progress(p: int):
        sys.stderr.write(f"\rProgress: {p}%")
        sys.stderr.flush()
        if p == 100:
            sys.stderr.write("\n")
            sys.stderr.flush()

    worker.progress_changed.connect(on_progress)
    # Calling run() is intentional: a CLI has no Qt event loop and must wait for
    # conversion completion. ConversionWorker still owns all FFmpeg work.
    worker.run()
    return result["success"]


def _detect_category(path: Path) -> Optional[str]:
    extension = path.suffix.lower()
    if extension in VIDEO_EXTENSIONS:
        return CATEGORY_VIDEO
    if extension in AUDIO_EXTENSIONS:
        return CATEGORY_AUDIO
    if extension in IMAGE_EXTENSIONS:
        return CATEGORY_IMAGE
    return None
