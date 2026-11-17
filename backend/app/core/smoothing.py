"""Module lọc nhiễu tín hiệu động học (Signal Smoothing Engine).

Sử dụng bộ lọc đa thức Savitzky-Golay để khử rung lắc (jitter) từ camera và mô hình MediaPipe,
bảo toàn nguyên vẹn độ sâu và vị trí đỉnh/đáy của các góc chuyển động.
"""

from typing import List, Dict, Any, Union
import numpy as np
from scipy.signal import savgol_filter


def _interpolate_nans(arr: np.ndarray) -> np.ndarray:
    """Nội suy các giá trị NaN trong mảng 1D bằng phương pháp tuyến tính."""
    nan_mask = np.isnan(arr)
    if not np.any(nan_mask):
        return arr.copy()

    valid_indices = np.where(~nan_mask)[0]
    if len(valid_indices) == 0:
        return np.zeros_like(arr)

    arr_clean = arr.copy()
    all_indices = np.arange(len(arr))
    arr_clean[nan_mask] = np.interp(
        all_indices[nan_mask],
        all_indices[~nan_mask],
        arr[~nan_mask]
    )
    return arr_clean


def smooth_signal_1d(
    signal: Union[List[float], np.ndarray],
    window_length: int = 11,
    polyorder: int = 2
) -> np.ndarray:
    """Lọc mượt chuỗi tín hiệu 1D (ví dụ: góc khớp theo thời gian) bằng Savitzky-Golay.

    Tự động xử lý các trường hợp biên:
    - NaN trong chuỗi được nội suy trước khi lọc.
    - Đảm bảo window_length là số lẻ và thỏa mãn polyorder < window_length <= len(signal).
    """
    arr = np.asarray(signal, dtype=np.float64)
    n = len(arr)

    if n <= polyorder + 1:
        return arr.copy()

    # Nội suy NaN nếu có
    clean_arr = _interpolate_nans(arr)

    # Đảm bảo window_length là số lẻ
    win = window_length if window_length % 2 == 1 else window_length + 1

    # Điều chỉnh nếu chuỗi ngắn hơn window_length
    if win > n:
        win = n if n % 2 == 1 else n - 1

    if win <= polyorder:
        win = polyorder + 2 if (polyorder + 2) % 2 == 1 else polyorder + 3
        if win > n:
            return clean_arr

    try:
        smoothed = savgol_filter(clean_arr, window_length=win, polyorder=polyorder)
        return smoothed
    except Exception:
        return clean_arr


def moving_average_1d(
    signal: Union[List[float], np.ndarray],
    window_size: int = 5
) -> np.ndarray:
    """Bộ lọc trung bình trượt (Moving Average) dùng để so sánh đối chứng trong thực nghiệm."""
    arr = np.asarray(signal, dtype=np.float64)
    clean_arr = _interpolate_nans(arr)
    if len(clean_arr) < window_size or window_size <= 1:
        return clean_arr.copy()

    kernel = np.ones(window_size) / window_size
    smoothed = np.convolve(clean_arr, kernel, mode="same")
    return smoothed


def smooth_landmarks_trajectory(
    frames_landmarks: List[List[Dict[str, Any]]],
    window_length: int = 11,
    polyorder: int = 2
) -> List[List[Dict[str, Any]]]:
    """Lọc mượt trực tiếp chuỗi tọa độ (x, y, z) của từng khớp mốc qua các khung hình."""
    if not frames_landmarks or len(frames_landmarks) <= polyorder + 1:
        return frames_landmarks

    num_frames = len(frames_landmarks)
    num_joints = len(frames_landmarks[0])

    # Ma trận chứa x, y, z của từng khớp theo thời gian: [num_joints, num_frames]
    x_matrix = np.zeros((num_joints, num_frames), dtype=np.float64)
    y_matrix = np.zeros((num_joints, num_frames), dtype=np.float64)
    z_matrix = np.zeros((num_joints, num_frames), dtype=np.float64)

    for f_idx, frame in enumerate(frames_landmarks):
        for j_idx, lm in enumerate(frame):
            x_matrix[j_idx, f_idx] = lm.get("x", 0.0)
            y_matrix[j_idx, f_idx] = lm.get("y", 0.0)
            z_matrix[j_idx, f_idx] = lm.get("z", 0.0)

    # Lọc mượt từng khớp
    for j_idx in range(num_joints):
        x_matrix[j_idx, :] = smooth_signal_1d(x_matrix[j_idx, :], window_length, polyorder)
        y_matrix[j_idx, :] = smooth_signal_1d(y_matrix[j_idx, :], window_length, polyorder)
        z_matrix[j_idx, :] = smooth_signal_1d(z_matrix[j_idx, :], window_length, polyorder)

    # Tái tạo lại cấu trúc danh sách
    result_frames: List[List[Dict[str, Any]]] = []
    for f_idx in range(num_frames):
        current_frame: List[Dict[str, Any]] = []
        for j_idx in range(num_joints):
            original = frames_landmarks[f_idx][j_idx]
            new_lm = dict(original)
            new_lm["x"] = float(x_matrix[j_idx, f_idx])
            new_lm["y"] = float(y_matrix[j_idx, f_idx])
            new_lm["z"] = float(z_matrix[j_idx, f_idx])
            current_frame.append(new_lm)
        result_frames.append(current_frame)

    return result_frames
