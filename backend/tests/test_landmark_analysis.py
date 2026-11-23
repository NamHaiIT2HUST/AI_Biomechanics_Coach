import pytest
from app.core.landmark_analysis import analyze_landmarks


def frames():
    joints = {"shoulder": (0.5, 0.1), "hip": (0.5, 0.4), "knee": (0.5, 0.7), "ankle": (0.5, 0.9)}
    data = []
    for i in range(15):
        landmarks = [dict(name="right_" + name, x=x, y=y, visibility=0.3 if i == 5 and name == "knee" else 0.9) for name, (x, y) in joints.items()]
        data.append(dict(frame_idx=i, is_detected=True, landmarks=landmarks))
    return {"fps": 30, "width": 720, "height": 1280, "dominant_side": "right", "frames": data}


def test_low_visibility_is_reported_without_inventing_reps():
    result = analyze_landmarks(frames())
    assert result["low_visibility_frames"] == 1
    assert result["reps"] == []
    assert "dưới ngưỡng" in result["warning"]


def test_missing_frame_does_not_silently_change_timing():
    data = frames()
    del data["frames"][4]
    with pytest.raises(ValueError, match="liên tục"):
        analyze_landmarks(data)


def test_missing_pose_is_not_interpolated_as_reliable():
    data = frames()
    data["frames"][5]["is_detected"] = False
    with pytest.raises(ValueError, match="thiếu pose"):
        analyze_landmarks(data)


def test_low_visibility_in_smoothing_window_marks_rep_for_review():
    import numpy as np
    angles = np.r_[np.full(8, 170.), np.linspace(170, 80, 20, endpoint=False),
                   np.linspace(80, 170, 21), np.full(8, 170.)]
    data = {"fps": 30, "width": 1000, "height": 1000, "dominant_side": "right", "frames": []}
    for i, angle in enumerate(angles):
        rad = np.radians(angle)
        hx, hy = 0.5 + 0.2 * np.sin(rad), 0.5 + 0.2 * np.cos(rad)
        joints = {"shoulder": (hx, hy - 0.2), "hip": (hx, hy), "knee": (0.5, 0.5), "ankle": (0.5, 0.7)}
        points = [dict(name="right_" + name, x=x, y=y, visibility=0.2 if i == 25 and name == "knee" else 0.9) for name, (x, y) in joints.items()]
        data["frames"].append(dict(frame_idx=i, is_detected=True, landmarks=points))
    result = analyze_landmarks(data)
    assert len(result["reps"]) == 1
    assert result["reps"][0]["quality_status"] == "needs_review"
    assert result["reps"][0]["low_visibility_in_filter_window"] == 1
    data["frames"][25]["landmarks"][2]["visibility"] = 0.9
    assert analyze_landmarks(data)["reps"][0]["quality_status"] == "no_low_visibility_detected"


def test_smoothing_support_accounts_for_edge_polynomial_window():
    from app.core.landmark_analysis import _smoothing_support
    assert _smoothing_support(0, 2, 20) == (0, 10)
    assert _smoothing_support(17, 19, 20) == (9, 19)
    assert _smoothing_support(8, 10, 20) == (3, 15)
    assert _smoothing_support(0, 1, 3) == (0, 1)
