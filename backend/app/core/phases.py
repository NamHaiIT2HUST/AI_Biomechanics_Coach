"""Phân đoạn squat từ chuỗi góc gối đã lọc.

Một rep hoàn chỉnh cần bắt đầu ở tư thế đứng, có đáy nổi bật dưới ngưỡng
và trở về tư thế đứng. Các ngưỡng không phải đánh giá chất lượng động tác.
"""
from dataclasses import dataclass
from enum import Enum
from math import ceil
from typing import Optional, Sequence

import numpy as np
from scipy.signal import find_peaks


class SquatPhase(str, Enum):
    SETUP = "setup"
    ECCENTRIC = "eccentric"
    BOTTOM = "bottom"
    CONCENTRIC = "concentric"
    LOCKOUT = "lockout"


@dataclass
class RepData:
    rep_id: int
    start_frame: int
    bottom_frame: int
    end_frame: int
    start_time_s: float
    bottom_time_s: float
    end_time_s: float
    eccentric_duration_s: float
    pause_duration_s: float
    concentric_duration_s: float
    total_duration_s: float
    min_knee_angle: float
    max_trunk_lean: Optional[float]
    trunk_lean_at_bottom: Optional[float]
    max_knee_over_toe_px: Optional[float]
    max_heel_rise_px: Optional[float]


def segment_squat_reps(
    knee_angles: Sequence[float],
    fps: float,
    hip_angles: Optional[Sequence[float]] = None,
    trunk_lean: Optional[Sequence[float]] = None,
    knee_over_toe_px: Optional[Sequence[float]] = None,
    heel_rise_px: Optional[Sequence[float]] = None,
    *,
    bottom_threshold: float = 105.0,
    standing_threshold: float = 160.0,
    prominence: float = 15.0,
    min_duration_s: float = 1.0,
    pause_tolerance_deg: float = 2.0,
) -> tuple[list[RepData], list[SquatPhase]]:
    """Return (completed reps, one phase per input frame).

    Knee angles must be finite; callers must handle missing observations before
    segmentation. Optional measurements may contain NaNs and yield None when
    absent. Frame numbers are zero-based indices in the input. Lockout labels
    require measured hip extension; knee extension alone completes a rep.

    Pause is the contiguous interval around the minimum within the configured
    tolerance. Its duration overlaps the eccentric/concentric durations, which
    are measured to/from the bottom frame as specified.
    """
    if not np.isfinite(fps) or fps <= 0:
        raise ValueError("fps must be positive and finite")
    if not (0 <= bottom_threshold < standing_threshold <= 180):
        raise ValueError("thresholds must satisfy 0 <= bottom < standing <= 180")
    if not np.isfinite(prominence) or prominence <= 0 or not np.isfinite(min_duration_s) or min_duration_s <= 0:
        raise ValueError("prominence and min_duration_s must be positive and finite")
    if not np.isfinite(pause_tolerance_deg) or pause_tolerance_deg < 0:
        raise ValueError("pause_tolerance_deg must be nonnegative and finite")
    knee = np.asarray(knee_angles, dtype=float)
    if knee.ndim != 1 or not np.all(np.isfinite(knee)):
        raise ValueError("knee_angles must be a finite one-dimensional sequence")
    n = len(knee)
    def optional(values, name):
        if values is None:
            return None
        arr = np.asarray(values, dtype=float)
        if arr.ndim != 1 or len(arr) != n or np.any(np.isinf(arr)):
            raise ValueError(f"{name} must match knee_angles and contain no infinities")
        return arr
    hip = optional(hip_angles, "hip_angles")
    trunk = optional(trunk_lean, "trunk_lean")
    toe = optional(knee_over_toe_px, "knee_over_toe_px")
    heel = optional(heel_rise_px, "heel_rise_px")
    phases = [SquatPhase.SETUP] * n
    if n == 0:
        return [], phases
    peaks, _ = find_peaks(-knee, prominence=prominence, distance=max(1, ceil(fps)))
    peak_set = set(peaks.tolist())
    reps = []
    # FSM: wait for standing, descend, then finish once standing is regained.
    state = "waiting"
    start = None
    candidates = []
    for i, angle in enumerate(knee):
        if state == "waiting":
            if angle >= standing_threshold:
                state = "standing"
                start = i
        elif state == "standing":
            if angle >= standing_threshold:
                start = i
            else:
                state = "moving"
                candidates = []
        elif state == "moving":
            if i in peak_set and angle < bottom_threshold:
                candidates.append(i)
            if angle >= standing_threshold:
                if candidates and (i - start) / fps >= min_duration_s:
                    bottom = min(candidates, key=lambda j: knee[j])
                    lo = hi = bottom
                    while lo > start and knee[lo - 1] <= knee[bottom] + pause_tolerance_deg:
                        lo -= 1
                    while hi < i and knee[hi + 1] <= knee[bottom] + pause_tolerance_deg:
                        hi += 1
                    def maximum(arr):
                        if arr is None:
                            return None
                        segment = arr[start:i + 1]
                        valid = segment[np.isfinite(segment)]
                        return float(np.max(valid)) if len(valid) else None
                    at_bottom = None if trunk is None or not np.isfinite(trunk[bottom]) else float(trunk[bottom])
                    reps.append(RepData(
                        len(reps) + 1, start, bottom, i, start / fps, bottom / fps, i / fps,
                        (bottom - start) / fps, (hi - lo) / fps, (i - bottom) / fps,
                        (i - start) / fps, float(knee[bottom]), maximum(trunk), at_bottom,
                        maximum(toe), maximum(heel)))
                    phases[start:lo] = [SquatPhase.ECCENTRIC] * (lo - start)
                    phases[lo:hi + 1] = [SquatPhase.BOTTOM] * (hi - lo + 1)
                    phases[hi + 1:i] = [SquatPhase.CONCENTRIC] * (i - hi - 1)
                state = "standing"
                start = i
    # Lockout is a measured posture, not a replacement for completion criterion.
    if hip is not None:
        for i in range(n):
            if knee[i] >= standing_threshold and np.isfinite(hip[i]) and hip[i] >= 165 and phases[i] == SquatPhase.SETUP:
                phases[i] = SquatPhase.LOCKOUT
    return reps, phases
