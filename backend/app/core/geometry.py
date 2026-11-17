"""Module tính toán động học và hình học sinh cơ học (Kinematics & Geometry Engine).

Cung cấp các hàm đo góc giải phẫu cơ thể học (góc gối, góc hông, góc nghiêng thân),
độ dốc các phân đoạn cơ thể, khoảng cách tương đối và tự động phát hiện bên thuận quan sát.
"""

from typing import Union, Dict, Any, List, Optional, Tuple
import numpy as np

PointLike = Union[np.ndarray, List[float], Tuple[float, ...], Dict[str, Any]]


def _to_numpy_point(p: PointLike, dim: int = 2) -> np.ndarray:
    """Chuyển đổi các định dạng điểm khác nhau (dict, list, tuple, object) thành numpy array."""
    if isinstance(p, np.ndarray):
        arr = p.astype(np.float64)
        return arr[:dim]

    if isinstance(p, (list, tuple)):
        return np.array(p[:dim], dtype=np.float64)

    if isinstance(p, dict):
        if dim == 2:
            return np.array([float(p["x"]), float(p["y"])], dtype=np.float64)
        return np.array([float(p["x"]), float(p["y"]), float(p.get("z", 0.0))], dtype=np.float64)

    if hasattr(p, "x") and hasattr(p, "y"):
        if dim == 2:
            return np.array([float(p.x), float(p.y)], dtype=np.float64)
        return np.array([float(p.x), float(p.y), float(getattr(p, "z", 0.0))], dtype=np.float64)

    raise ValueError(f"Không thể chuyển đổi điểm dạng: {type(p)}")


def calculate_angle_2d(a: PointLike, b: PointLike, c: PointLike) -> float:
    """Tính góc 2D (độ) giữa 3 điểm A, B, C với đỉnh tại B.

    Góc nằm trong khoảng [0.0, 180.0].
    Vector u = A - B
    Vector v = C - B
    cos(theta) = (u . v) / (||u|| * ||v||)
    """
    pt_a = _to_numpy_point(a, dim=2)
    pt_b = _to_numpy_point(b, dim=2)
    pt_c = _to_numpy_point(c, dim=2)

    ba = pt_a - pt_b
    bc = pt_c - pt_b

    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)

    if norm_ba < 1e-7 or norm_bc < 1e-7:
        return 0.0

    cosine = np.dot(ba, bc) / (norm_ba * norm_bc)
    cosine = np.clip(cosine, -1.0, 1.0)
    angle_rad = np.arccos(cosine)
    return float(np.degrees(angle_rad))


def calculate_angle_3d(a: PointLike, b: PointLike, c: PointLike) -> float:
    """Tính góc không gian 3D (độ) giữa 3 điểm A, B, C với đỉnh tại B."""
    pt_a = _to_numpy_point(a, dim=3)
    pt_b = _to_numpy_point(b, dim=3)
    pt_c = _to_numpy_point(c, dim=3)

    ba = pt_a - pt_b
    bc = pt_c - pt_b

    norm_ba = np.linalg.norm(ba)
    norm_bc = np.linalg.norm(bc)

    if norm_ba < 1e-7 or norm_bc < 1e-7:
        return 0.0

    cosine = np.dot(ba, bc) / (norm_ba * norm_bc)
    cosine = np.clip(cosine, -1.0, 1.0)
    angle_rad = np.arccos(cosine)
    return float(np.degrees(angle_rad))


def calculate_trunk_lean(
    shoulder: PointLike,
    hip: PointLike,
    coordinate_system: str = "image"
) -> float:
    """Tính độ nghiêng của thân trên (cột sống) so với phương thẳng đứng (đơn vị: độ).

    Trong hệ tọa độ ảnh (image coordinates):
    - Trục X hướng sang phải [1, 0].
    - Trục Y hướng xuống dưới [0, 1].
    - Vector phương thẳng đứng hướng lên trời là [0, -1].
    """
    pt_shoulder = _to_numpy_point(shoulder, dim=2)
    pt_hip = _to_numpy_point(hip, dim=2)

    torso_vector = pt_shoulder - pt_hip
    norm_torso = np.linalg.norm(torso_vector)

    if norm_torso < 1e-7:
        return 0.0

    if coordinate_system == "image":
        vertical_vector = np.array([0.0, -1.0], dtype=np.float64)
    else:
        vertical_vector = np.array([0.0, 1.0], dtype=np.float64)

    cosine = np.dot(torso_vector, vertical_vector) / norm_torso
    cosine = np.clip(cosine, -1.0, 1.0)
    angle_deg = float(np.degrees(np.arccos(cosine)))
    return angle_deg


def calculate_femur_angle(
    hip: PointLike,
    knee: PointLike,
    coordinate_system: str = "image"
) -> float:
    """Tính góc của xương đùi (hip -> knee) so với phương nằm ngang.

    Giúp xác định điểm phá vỡ song song (Break Parallel) của squat.
    Nếu góc âm hoặc nếp gấp hông nằm dưới gối: đã phá vỡ song song.
    """
    pt_hip = _to_numpy_point(hip, dim=2)
    pt_knee = _to_numpy_point(knee, dim=2)

    femur = pt_knee - pt_hip
    norm_femur = np.linalg.norm(femur)

    if norm_femur < 1e-7:
        return 0.0

    # Góc so với trục ngang
    dx = abs(femur[0])
    dy = femur[1] if coordinate_system == "image" else -femur[1]
    angle_rad = np.arctan2(dy, dx)
    return float(np.degrees(angle_rad))


def calculate_knee_over_toe(
    knee: PointLike,
    toe: PointLike,
    width: float = 1.0,
    facing: str = "auto"
) -> float:
    """Tính khoảng cách đầu gối nhô qua mũi chân theo phương ngang (pixels hoặc chuẩn hóa).

    Giá trị dương thể hiện đầu gối vượt quá mũi chân.
    """
    pt_knee = _to_numpy_point(knee, dim=2)
    pt_toe = _to_numpy_point(toe, dim=2)

    diff_x = (pt_knee[0] - pt_toe[0]) * width

    # Nếu facing auto, ta giả định hướng dương là hướng tiến về phía mũi chân
    return float(diff_x)


def calculate_heel_rise(
    heel_setup_y: float,
    heel_current_y: float,
    height: float = 1.0,
    coordinate_system: str = "image"
) -> float:
    """Tính độ cao gót chân bị nâng lên khỏi sàn nhà (pixels hoặc chuẩn hóa).

    Trong hệ tọa độ ảnh, Y=0 ở trên cùng, Y=Height ở dưới sàn.
    Khi gót nhấc lên, heel_current_y < heel_setup_y, độ chênh lệch là (heel_setup_y - heel_current_y).
    """
    if coordinate_system == "image":
        diff_y = (heel_setup_y - heel_current_y) * height
    else:
        diff_y = (heel_current_y - heel_setup_y) * height

    return float(max(0.0, diff_y))


def detect_dominant_side(
    frames: List[Any],
    min_confidence: float = 0.5
) -> str:
    """Tự động phân tích toàn bộ video để xác định hướng người tập quay về phía camera.

    So sánh điểm số `visibility` trung bình giữa 4 khớp chính của thân Trái và thân Phải:
    (vai, hông, gối, cổ chân).
    Trả về: 'right' hoặc 'left'.
    """
    left_joints = ["left_hip", "left_knee", "left_ankle", "left_shoulder"]
    right_joints = ["right_hip", "right_knee", "right_ankle", "right_shoulder"]

    left_scores: List[float] = []
    right_scores: List[float] = []

    for f in frames:
        if not getattr(f, "is_detected", True):
            continue

        l_vals: List[float] = []
        r_vals: List[float] = []

        for j in left_joints:
            lm = f.get_landmark(j) if hasattr(f, "get_landmark") else None
            if lm and "visibility" in lm:
                l_vals.append(float(lm["visibility"]))

        for j in right_joints:
            lm = f.get_landmark(j) if hasattr(f, "get_landmark") else None
            if lm and "visibility" in lm:
                r_vals.append(float(lm["visibility"]))

        if l_vals:
            left_scores.append(float(np.mean(l_vals)))
        if r_vals:
            right_scores.append(float(np.mean(r_vals)))

    mean_left = float(np.mean(left_scores)) if left_scores else 0.0
    mean_right = float(np.mean(right_scores)) if right_scores else 0.0

    return "right" if mean_right >= mean_left else "left"
