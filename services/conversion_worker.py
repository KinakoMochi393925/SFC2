"""FFmpeg による変換をバックグラウンドスレッドで実行する。UIをフリーズさせない。

目標ファイルサイズが指定されている場合は、事前にビットレートプランを算出し、
必要に応じて2パスエンコードを行う。
"""
import glob
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import QThread, pyqtSignal

from models.conversion_settings import ConversionSettings
from services.bitrate_calculator import BitratePlan, calculate_bitrate_plan
from services.ffmpeg_command_builder import build_command, get_output_extension, needs_two_pass
from services.media_probe import probe_media
from utils.constants import PRIORITY_QUALITY
from utils.filename_utils import generate_unique_output_path
from utils.i18n import tr
from utils.logger import get_logger

_TIME_RE = re.compile(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)")
_DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")

_MIN_FREE_BYTES = 20 * 1024 * 1024  # 20MB を下回ったら警告


def _to_seconds(h: str, m: str, s: str) -> float:
    return int(h) * 3600 + int(m) * 60 + float(s)


def _null_output() -> str:
    return "NUL" if sys.platform == "win32" else "/dev/null"


class ConversionWorker(QThread):
    progress_changed = pyqtSignal(int)
    finished_signal = pyqtSignal(bool, str, str)  # success, output_path, error_message
    size_warning = pyqtSignal(str)  # 目標サイズが小さすぎる場合の警告（引数はMB表記の文字列）

    def __init__(self, ffmpeg_path: str, settings: ConversionSettings, parent=None):
        super().__init__(parent)
        self._ffmpeg_path = ffmpeg_path
        self._settings = settings
        self._process = None

    def stop(self) -> None:
        """実行中の FFmpeg を停止し、スレッドを自然終了させる。"""
        self.requestInterruption()
        process = self._process
        if process is not None and process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass

    # ------------------------------------------------------------------
    def run(self) -> None:
        logger = get_logger()
        settings = self._settings
        output_dir = Path(settings.output_dir)

        try:
            if not output_dir.exists():
                self.finished_signal.emit(False, "", tr("error_output_dir_missing"))
                return

            try:
                usage = shutil.disk_usage(output_dir)
                if usage.free < _MIN_FREE_BYTES:
                    self.finished_signal.emit(False, "", tr("error_disk_space"))
                    return
            except OSError:
                pass  # 容量チェック自体が失敗しても変換は試みる

            extension = get_output_extension(settings.output_format)
            output_path = generate_unique_output_path(
                str(output_dir), settings.output_stem, extension
            )

            if Path(settings.input_path).resolve() == output_path.resolve():
                self.finished_signal.emit(False, "", tr("error_same_as_input"))
                return

            bitrate_plan = self._build_bitrate_plan_if_needed(settings)
            if bitrate_plan is None and self._plan_rejected:
                return  # 警告シグナル発行済み・変換は開始しない

            two_pass = needs_two_pass(settings, bitrate_plan)
            duration_hint = self._known_duration

            if two_pass:
                success = self._run_two_pass(output_path, settings, bitrate_plan, duration_hint)
            else:
                cmd = build_command(
                    self._ffmpeg_path, output_path, settings, bitrate_plan,
                    null_output=_null_output(),
                )
                logger.info("FFmpeg command: %s", " ".join(cmd))
                success = self._run_ffmpeg(cmd, progress_range=(0, 100), known_duration=duration_hint)

            if success and output_path.exists():
                self.progress_changed.emit(100)
                self.finished_signal.emit(True, str(output_path), "")
            elif success:
                self.finished_signal.emit(False, "", tr("error_generic_conversion"))

        except OSError as e:
            logger.exception("OSError during conversion")
            self.finished_signal.emit(False, "", tr("error_file_operation", error=str(e)))
        except Exception as e:  # 想定外の例外もすべてダイアログへ伝える
            logger.exception("Unexpected error during conversion")
            self.finished_signal.emit(False, "", tr("error_unexpected", error=str(e)))

    # ------------------------------------------------------------------
    # 目標ファイルサイズ指定時のビットレートプラン算出
    # ------------------------------------------------------------------
    def _build_bitrate_plan_if_needed(self, settings: ConversionSettings) -> Optional[BitratePlan]:
        self._plan_rejected = False
        self._known_duration = None

        gif_selected = settings.output_format.lower() == "gif"
        if not settings.target_size_bytes or settings.category not in ("video", "audio") or gif_selected:
            return None

        media_info = probe_media(self._ffmpeg_path, settings.input_path)
        if not media_info.duration_seconds or media_info.duration_seconds <= 0:
            self._plan_rejected = True
            self.finished_signal.emit(False, "", tr("error_probe_failed"))
            return None

        self._known_duration = media_info.duration_seconds

        plan = calculate_bitrate_plan(
            target_size_bytes=settings.target_size_bytes,
            duration_seconds=media_info.duration_seconds,
            priority=settings.priority or PRIORITY_QUALITY,
            source_width=media_info.width,
            source_height=media_info.height,
            source_fps=None,
            audio_only=(settings.category == "audio"),
        )

        if plan.is_critical:
            self._plan_rejected = True
            size_mb = round(settings.target_size_bytes / (1024 * 1024), 2)
            self.size_warning.emit(str(size_mb))
            return None

        return plan

    # ------------------------------------------------------------------
    # 2パスエンコード
    # ------------------------------------------------------------------
    def _run_two_pass(
        self,
        output_path: Path,
        settings: ConversionSettings,
        bitrate_plan: BitratePlan,
        duration_hint: Optional[float],
    ) -> bool:
        logger = get_logger()
        passlog_prefix = str(Path(settings.output_dir) / f"{settings.output_stem}_ffpass")

        cmd1 = build_command(
            self._ffmpeg_path, output_path, settings, bitrate_plan,
            pass_number=1, passlog_prefix=passlog_prefix, null_output=_null_output(),
        )
        logger.info("FFmpeg pass1 command: %s", " ".join(cmd1))
        ok = self._run_ffmpeg(cmd1, progress_range=(0, 50), known_duration=duration_hint)
        if not ok:
            self._cleanup_passlogs(passlog_prefix)
            return False

        cmd2 = build_command(
            self._ffmpeg_path, output_path, settings, bitrate_plan,
            pass_number=2, passlog_prefix=passlog_prefix, null_output=_null_output(),
        )
        logger.info("FFmpeg pass2 command: %s", " ".join(cmd2))
        ok = self._run_ffmpeg(cmd2, progress_range=(50, 100), known_duration=duration_hint)
        self._cleanup_passlogs(passlog_prefix)
        return ok

    @staticmethod
    def _cleanup_passlogs(prefix: str) -> None:
        for path in glob.glob(f"{prefix}*"):
            try:
                os.remove(path)
            except OSError:
                pass

    # ------------------------------------------------------------------
    # FFmpegプロセスの実行と進捗解析
    # ------------------------------------------------------------------
    def _run_ffmpeg(
        self, cmd: List[str], progress_range: tuple, known_duration: Optional[float]
    ) -> bool:
        logger = get_logger()
        popen_kwargs = dict(
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            encoding="utf-8",
            errors="replace",
        )
        if sys.platform == "win32":
            popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

        try:
            self._process = subprocess.Popen(cmd, **popen_kwargs)
        except FileNotFoundError:
            self.finished_signal.emit(False, "", tr("error_ffmpeg_missing"))
            return False
        except PermissionError:
            self.finished_signal.emit(False, "", tr("error_output_dir_no_permission"))
            return False

        total_seconds = known_duration
        range_start, range_end = progress_range
        tail_lines: List[str] = []

        for line in self._process.stderr:
            if self.isInterruptionRequested():
                self.stop()

            tail_lines.append(line)
            if len(tail_lines) > 40:
                tail_lines.pop(0)

            if total_seconds is None:
                m = _DURATION_RE.search(line)
                if m:
                    total_seconds = _to_seconds(*m.groups())

            m2 = _TIME_RE.search(line)
            if m2 and total_seconds:
                current = _to_seconds(*m2.groups())
                fraction = max(0.0, min(1.0, current / total_seconds))
                pct = int(range_start + fraction * (range_end - range_start))
                self.progress_changed.emit(max(0, min(99, pct)))

        returncode = self._process.wait()
        self._process = None

        if self.isInterruptionRequested():
            return False

        if returncode == 0:
            return True

        error_text = "".join(tail_lines).strip()
        logger.error("FFmpeg failed (code=%s): %s", returncode, error_text)
        self.finished_signal.emit(False, "", error_text or tr("error_generic_conversion"))
        return False