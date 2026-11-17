"""Baseline có thể chạy lại trên JSON landmark, kèm cảnh báo độ tin cậy.

Chạy: python -m app.core.landmark_analysis path.json [--min-duration 0.9]
Đây là phân tích thử nghiệm, không phải kết luận về kỹ thuật hay an toàn.
"""
import argparse
from dataclasses import asdict
import json
from pathlib import Path

import numpy as np

from app.core.geometry import calculate_angle_2d, calculate_trunk_lean
from app.core.phases import segment_squat_reps
from app.core.smoothing import smooth_signal_1d


def analyze_landmarks(data, *, min_duration_s=1.0, min_visibility=0.5):
    """Phân tích frame liên tục; giữ cảnh báo kể cả khi vẫn tính trên điểm yếu."""
    fps = float(data["fps"])
    width, height = float(data["width"]), float(data["height"])
    if not np.isfinite(fps) or fps <= 0 or not np.isfinite(width) or not np.isfinite(height) or width <= 0 or height <= 0:
        raise ValueError("FPS và kích thước ảnh phải dương và hữu hạn")
    if not 0 <= min_visibility <= 1:
        raise ValueError("min_visibility phải nằm trong [0, 1]")
    frames = data["frames"]
    if not frames:
        raise ValueError("Không có frame landmark")
    if any(frame.get("frame_idx") != i for i, frame in enumerate(frames)):
        raise ValueError("frame_idx phải liên tục từ 0; không được nén frame mất")
    joint_names = ("shoulder", "hip", "knee", "ankle")
    # Ưu tiên bên được lưu trong kết quả; nếu chưa có, chọn bên có visibility trung bình cao hơn.
    side = data.get("dominant_side")
    if side is None:
        scores = {}
        for candidate in ("left", "right"):
            values = []
            for frame in frames:
                by_name = {p.get("name"): p for p in frame.get("landmarks", [])}
                values.extend(float(by_name.get(candidate + "_" + name, {}).get("visibility", 0)) for name in joint_names)
            scores[candidate] = float(np.mean(values))
        side = max(scores, key=scores.get)
    if side not in ("left", "right"):
        raise ValueError("dominant_side phải là left hoặc right")
    knee, hip, trunk = [], [], []
    low_visibility = []
    for i, frame in enumerate(frames):
        points = {p.get("name"): p for p in frame.get("landmarks", [])}
        names = [side + "_" + joint for joint in joint_names]
        if not frame.get("is_detected") or any(name not in points for name in names):
            raise ValueError(f"Frame {i} thiếu pose hoặc khớp; chưa hỗ trợ nội suy có kiểm soát")
        coords, visibility = [], []
        for name in names:
            point = points[name]
            x, y, v = float(point["x"]), float(point["y"]), float(point.get("visibility", 0))
            if not np.isfinite([x, y, v]).all() or not 0 <= v <= 1:
                raise ValueError(f"Frame {i} có tọa độ hoặc visibility không hợp lệ")
            coords.append((x * width, y * height))
            visibility.append(v)
        if min(visibility) < min_visibility:
            low_visibility.append(i)
        knee.append(calculate_angle_2d(*coords[1:]))
        hip.append(calculate_angle_2d(*coords[:3]))
        trunk.append(calculate_trunk_lean(coords[0], coords[1]))
    knee, hip, trunk = (smooth_signal_1d(a) for a in (knee, hip, trunk))
    reps, _ = segment_squat_reps(knee, fps, hip_angles=hip, trunk_lean=trunk, min_duration_s=min_duration_s)
    low_set = set(low_visibility)
    results = []
    for rep in reps:
        row = asdict(rep)
        row["low_visibility_frames"] = sum(i in low_set for i in range(rep.start_frame, rep.end_frame + 1))
        # Savitzky–Golay uses an 11-frame window, so nearby low-quality points can affect the result.
        row["low_visibility_near_bottom"] = any(i in low_set for i in range(max(0, rep.bottom_frame - 5), min(len(frames), rep.bottom_frame + 6)))
        results.append(row)
    return {
        "video_name": data.get("video_name"), "fps": fps, "dominant_side": side,
        "frames": len(frames), "min_visibility": min_visibility,
        "low_visibility_frames": len(low_visibility), "min_duration_s": min_duration_s,
        "warning": "Landmark dưới ngưỡng vẫn được dùng; kết quả chỉ để khảo sát, chưa được kiểm chứng." if low_visibility else "Kết quả chưa được kiểm chứng bằng nhãn độc lập.",
        "reps": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--min-duration", type=float, default=1.0)
    parser.add_argument("--min-visibility", type=float, default=0.5)
    args = parser.parse_args()
    data = json.loads(args.path.read_text(encoding="utf-8"))
    print(json.dumps(analyze_landmarks(data, min_duration_s=args.min_duration, min_visibility=args.min_visibility), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
