"""目標ファイルサイズ指定時のビットレート配分アルゴリズム。

処理の流れ:
  1. 目標合計ビットレート = 目標サイズ(bytes)*8 / 動画長(秒) * 0.95
  2. 優先度に応じて音声ビットレートを確保し、残りを映像に割り振る
  3. BPP (映像ビットレート / (幅*高さ*fps)) が閾値を下回る場合、
     fps → 解像度の順に段階的に下げて安全域まで調整する
  4. 最低ラインまで下げてもなお危険域の場合は警告フラグを立てる
"""
import re
from dataclasses import dataclass
from typing import Optional

from utils.constants import (
    AUDIO_BITRATE_AUDIO_PRIORITY,
    AUDIO_BITRATE_QUALITY_PRIORITY,
    BPP_CRITICAL_MIN,
    BPP_SAFE_MIN,
    FPS_STEPS,
    PRIORITY_AUDIO,
    PRIORITY_QUALITY,
    RESOLUTION_STEPS,
)

_SIZE_RE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*(mb|gb|kb|m|g|k)?\s*$", re.IGNORECASE)

_UNIT_MULTIPLIERS = {
    "k": 1024,
    "kb": 1024,
    "m": 1024 * 1024,
    "mb": 1024 * 1024,
    "g": 1024 * 1024 * 1024,
    "gb": 1024 * 1024 * 1024,
    "": 1024 * 1024,  # 単位なしはMB扱い
}


def parse_target_size(text: str) -> Optional[int]:
    """"10MB" のような文字列をバイト数に変換する。不正な場合は None。"""
    if not text or not text.strip():
        return None
    match = _SIZE_RE.match(text)
    if not match:
        return None
    value, unit = match.groups()
    unit = (unit or "").lower()
    multiplier = _UNIT_MULTIPLIERS.get(unit)
    if multiplier is None:
        return None
    return int(float(value) * multiplier)


@dataclass
class BitratePlan:
    video_bitrate_bps: Optional[int]  # 音声のみの場合は None
    audio_bitrate_bps: int
    width: Optional[int]
    height: Optional[int]
    fps: Optional[int]
    bpp: Optional[float]
    is_critical: bool  # 最低ラインでも画質崩壊が避けられない
    warning_message_key: Optional[str] = None


def _fit_bpp_video(
    video_bitrate_bps: int, width: int, height: int, source_fps: Optional[float]
) -> tuple[int, int, int, float]:
    """fps→解像度の順に段階的に下げ、BPPが安全域に収まるパラメータを探す。"""
    fps_candidates = [f for f in FPS_STEPS if source_fps is None or f <= source_fps] or [FPS_STEPS[-1]]
    if source_fps and source_fps < fps_candidates[0]:
        fps_candidates = [source_fps] + fps_candidates

    resolution_candidates = [(w, h) for (w, h) in RESOLUTION_STEPS if w <= width or h <= height]
    if not resolution_candidates or resolution_candidates[0] != (width, height):
        resolution_candidates = [(width, height)] + resolution_candidates

    best = None
    for w, h in resolution_candidates:
        for fps in fps_candidates:
            bpp = video_bitrate_bps / (w * h * fps)
            if best is None or bpp > best[3]:
                best = (w, h, fps, bpp)
            if bpp >= BPP_SAFE_MIN:
                return (w, h, int(round(fps)), bpp)
    # 安全域に収まらなくても、最も良い組み合わせを返す
    return best


def calculate_bitrate_plan(
    target_size_bytes: int,
    duration_seconds: float,
    priority: str,
    source_width: Optional[int],
    source_height: Optional[int],
    source_fps: Optional[float] = None,
    audio_only: bool = False,
) -> BitratePlan:
    """目標ファイルサイズ・優先度から映像/音声ビットレート等を算出する。"""
    total_bitrate_bps = (target_size_bytes * 8 / duration_seconds) * 0.95

    if priority == PRIORITY_AUDIO:
        audio_min, audio_max = AUDIO_BITRATE_AUDIO_PRIORITY
    else:
        audio_min, audio_max = AUDIO_BITRATE_QUALITY_PRIORITY

    if audio_only:
        audio_bitrate = int(min(audio_max, max(audio_min, total_bitrate_bps)))
        return BitratePlan(
            video_bitrate_bps=None,
            audio_bitrate_bps=audio_bitrate,
            width=None,
            height=None,
            fps=None,
            bpp=None,
            is_critical=False,
        )

    # 音声ビットレートを確保し、残りを映像に割り振る
    audio_bitrate = int(min(audio_max, audio_min))
    if priority == PRIORITY_AUDIO:
        audio_bitrate = int(min(audio_max, max(audio_min, total_bitrate_bps * 0.25)))
        audio_bitrate = max(audio_min, min(audio_bitrate, audio_max))
    else:
        audio_bitrate = audio_min

    video_bitrate = max(1, int(total_bitrate_bps - audio_bitrate))

    width = source_width or 1920
    height = source_height or 1080
    fps = source_fps or 30

    fitted_width, fitted_height, fitted_fps, bpp = _fit_bpp_video(video_bitrate, width, height, fps)

    is_critical = bpp < BPP_CRITICAL_MIN
    warning_key = "size_warning_message" if bpp < BPP_SAFE_MIN else None

    return BitratePlan(
        video_bitrate_bps=video_bitrate,
        audio_bitrate_bps=audio_bitrate,
        width=fitted_width,
        height=fitted_height,
        fps=fitted_fps,
        bpp=bpp,
        is_critical=is_critical,
        warning_message_key=warning_key,
    )
