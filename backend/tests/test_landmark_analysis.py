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
