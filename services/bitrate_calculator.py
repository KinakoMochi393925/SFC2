"""目標ファイルサイズ指定時のビットレート配分アルゴリズム。

処理の流れ:
  1. 目標合計ビットレート = 目標サイズ(bytes)*8 / 動画長(秒) * 0.95
  2. 優先度に応じて音声ビットレートを確保し、残りを映像に割り振る
  3. BPP (映像ビットレート / (幅*高さ*fps)) が安全閾値を下回る場合、
     アスペクト比を維持したまま解像度・fpsを段階的に下げて調整する
  4. 最低ラインまで下げてもなお危険域の場合は警告フラグを立てる
"""
import re
from dataclasses import dataclass
from typing import Optional

from utils.constants import (
    AUDIO_BITRATE_AUDIO_PRIORITY,
    AUDIO_BITRATE_MIN_FALLBACK,
    AUDIO_BITRATE_QUALITY_PRIORITY,
    CODEC_BPP_SAFE_MAP,
    DEFAULT_BPP_CRITICAL_MIN,
    DEFAULT_BPP_SAFE_MIN,
    FPS_STEPS,
    PRIORITY_AUDIO,
    PRIORITY_QUALITY,
    TARGET_SHORT_SIDES,
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


def _build_resolution_candidates(width: int, height: int) -> list[tuple[int, int]]:
    """元のアスペクト比を維持しながら段階的な解像度候補を生成する（偶数ピクセル保証）。"""
    candidates = [(width, height)]
    min_side = min(width, height)
    aspect_ratio = width / height

    for target_short in TARGET_SHORT_SIDES:
        if target_short >= min_side:
            continue
        if width >= height:  # 横長
            new_h = target_short
            new_w = int(round(new_h * aspect_ratio))
        else:  # 縦長
            new_w = target_short
            new_h = int(round(new_w / aspect_ratio))

        # エンコーダ互換性のために偶数ピクセルに丸める
        new_w = new_w + (new_w % 2)
        new_h = new_h + (new_h % 2)

        if (new_w, new_h) not in candidates and new_w > 0 and new_h > 0:
            candidates.append((new_w, new_h))

    return candidates


def _build_fps_candidates(source_fps: Optional[float]) -> list[float]:
    """元fps以下のfps候補リストを生成する（降順）。"""
    if not source_fps or source_fps <= 0:
        return [30.0, 24.0]

    fps_list = []
    fps_list.append(source_fps)
    for f in FPS_STEPS:
        if f < source_fps and f not in fps_list:
            fps_list.append(float(f))

    if not fps_list:
        fps_list = [source_fps]
    return fps_list


def _fit_bpp_video(
    video_bitrate_bps: int,
    width: int,
    height: int,
    source_fps: Optional[float],
    safe_bpp: float = DEFAULT_BPP_SAFE_MIN,
) -> tuple[int, int, int, float]:
    """高解像度・高fpsから探索し、BPPが安全域に収まるパラメータを探す。"""
    fps_candidates = _build_fps_candidates(source_fps)
    resolution_candidates = _build_resolution_candidates(width, height)

    best_candidate = None  # 最も高いBPPを持つフォールバック候補

    for w, h in resolution_candidates:
        for fps in fps_candidates:
            bpp = video_bitrate_bps / (w * h * fps)
            if best_candidate is None or bpp > best_candidate[3]:
                best_candidate = (w, h, int(round(fps)), bpp)
            if bpp >= safe_bpp:
                return (w, h, int(round(fps)), bpp)

    return best_candidate


def calculate_bitrate_plan(
    target_size_bytes: int,
    duration_seconds: float,
    priority: str,
    source_width: Optional[int],
    source_height: Optional[int],
    source_fps: Optional[float] = None,
    audio_only: bool = False,
    video_codec: Optional[str] = None,
) -> BitratePlan:
    """目標ファイルサイズ・優先度から映像/音声ビットレート等を算出する。"""
    # 5%のマージンを引いて目標ビットレートを算出
    total_bitrate_bps = (target_size_bytes * 8 / duration_seconds) * 0.95

    if priority == PRIORITY_AUDIO:
        audio_min, audio_max = AUDIO_BITRATE_AUDIO_PRIORITY
    else:
        audio_min, audio_max = AUDIO_BITRATE_QUALITY_PRIORITY

    if audio_only:
        audio_bitrate = int(min(audio_max, max(AUDIO_BITRATE_MIN_FALLBACK, total_bitrate_bps)))
        return BitratePlan(
            video_bitrate_bps=None,
            audio_bitrate_bps=audio_bitrate,
            width=None,
            height=None,
            fps=None,
            bpp=None,
            is_critical=False,
        )

    # 音声ビットレートの配分（超低ビットレート時に映像ビットレートが枯渇しないよう動的に調整）
    if priority == PRIORITY_AUDIO:
        # 音声優先時は全体の30%〜40%を割り当て（最大192kbps、最低32kbps）
        target_audio = total_bitrate_bps * 0.35
        # 映像に最低50%残せるよう調整
        max_audio_allowed = max(AUDIO_BITRATE_MIN_FALLBACK, total_bitrate_bps * 0.5)
        audio_bitrate = int(min(audio_max, max(AUDIO_BITRATE_MIN_FALLBACK, min(target_audio, max_audio_allowed))))
    else:
        # 画質優先時は最小限の音声ビットレートを確保（全体の最大20%程度までに抑える）
        max_audio_allowed = max(AUDIO_BITRATE_MIN_FALLBACK, total_bitrate_bps * 0.2)
        audio_bitrate = int(min(audio_min, max(AUDIO_BITRATE_MIN_FALLBACK, max_audio_allowed)))

    video_bitrate = max(1, int(total_bitrate_bps - audio_bitrate))

    width = source_width or 1920
    height = source_height or 1080
    fps = source_fps or 30.0

    safe_bpp = CODEC_BPP_SAFE_MAP.get(video_codec, DEFAULT_BPP_SAFE_MIN)
    critical_bpp = safe_bpp * 0.5

    fitted_width, fitted_height, fitted_fps, bpp = _fit_bpp_video(
        video_bitrate, width, height, fps, safe_bpp=safe_bpp
    )

    is_critical = bpp < critical_bpp
    warning_key = "size_warning_message" if bpp < safe_bpp else None

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
