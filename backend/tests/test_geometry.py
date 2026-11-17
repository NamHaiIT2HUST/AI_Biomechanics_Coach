"""Unit tests cho module geometry và smoothing (Tầng 2)."""

import pytest
import numpy as np

from app.core.geometry import (
    calculate_angle_2d,
    calculate_angle_3d,
    calculate_trunk_lean,
    calculate_femur_angle,
    calculate_knee_over_toe,
    calculate_heel_rise,
    detect_dominant_side,
)
from app.core.smoothing import (
    smooth_signal_1d,
    moving_average_1d,
    smooth_landmarks_trajectory,
)


class TestGeometryAngles:
    """Kiểm tra tính toán góc 2D và 3D."""

    def test_right_angle_90_deg(self):
        # A=(0, 1), B=(0, 0), C=(1, 0) -> Tam giác vuông tại gốc tọa độ
        angle = calculate_angle_2d([0.0, 1.0], [0.0, 0.0], [1.0, 0.0])
        assert pytest.approx(angle, abs=1e-3) == 90.0

    def test_straight_line_180_deg(self):
        # A=(-1, 0), B=(0, 0), C=(1, 0) -> Đường thẳng duỗi 180 độ
        angle = calculate_angle_2d([-1.0, 0.0], [0.0, 0.0], [1.0, 0.0])
        assert pytest.approx(angle, abs=1e-3) == 180.0

    def test_zero_angle_0_deg(self):
        # A=(1, 0), B=(0, 0), C=(1, 0) -> 2 vector trùng nhau
        angle = calculate_angle_2d([1.0, 0.0], [0.0, 0.0], [1.0, 0.0])
        assert pytest.approx(angle, abs=1e-3) == 0.0

    def test_acute_angle_45_deg(self):
        # A=(1, 1), B=(0, 0), C=(1, 0)
        angle = calculate_angle_2d([1.0, 1.0], [0.0, 0.0], [1.0, 0.0])
        assert pytest.approx(angle, abs=1e-3) == 45.0

    def test_input_types_dict_and_objects(self):
        # Hỗ trợ dạng dict của MediaPipe
        pt_a = {"x": 0.0, "y": 1.0}
        pt_b = {"x": 0.0, "y": 0.0}
        pt_c = {"x": 1.0, "y": 0.0}
        angle = calculate_angle_2d(pt_a, pt_b, pt_c)
        assert pytest.approx(angle, abs=1e-3) == 90.0

    def test_zero_length_vector_no_crash(self):
        # Điểm A trùng điểm B -> Không bị lỗi chia cho 0
        angle = calculate_angle_2d([0.0, 0.0], [0.0, 0.0], [1.0, 0.0])
        assert angle == 0.0

    def test_angle_3d_orthogonal_axes(self):
        # Trục X và Trục Y trong không gian 3D
        angle = calculate_angle_3d([1.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 1.0, 0.0])
        assert pytest.approx(angle, abs=1e-3) == 90.0

    def test_angle_3d_straight(self):
        # Trục Z đi từ -1 đến +1 qua gốc tọa độ
        angle = calculate_angle_3d([0.0, 0.0, -1.0], [0.0, 0.0, 0.0], [0.0, 0.0, 1.0])
        assert pytest.approx(angle, abs=1e-3) == 180.0


class TestTrunkAndLimbKinematics:
    """Kiểm tra các góc giải phẫu và tư thế cơ thể."""

    def test_trunk_lean_upright(self):
        # Đứng thẳng trong hệ tọa độ ảnh: vai ở trên y=0.2, hông ở dưới y=0.8
        shoulder = {"x": 0.5, "y": 0.2}
        hip = {"x": 0.5, "y": 0.8}
        angle = calculate_trunk_lean(shoulder, hip, coordinate_system="image")
        assert pytest.approx(angle, abs=1e-3) == 0.0

    def test_trunk_lean_45_deg(self):
        # Nghiêng 45 độ
        shoulder = {"x": 0.8, "y": 0.5}
        hip = {"x": 0.5, "y": 0.8}
        angle = calculate_trunk_lean(shoulder, hip, coordinate_system="image")
        assert pytest.approx(angle, abs=1e-3) == 45.0

    def test_trunk_lean_horizontal_90_deg(self):
        # Gập lưng song song mặt đất (nghiêng 90 độ)
        shoulder = {"x": 0.8, "y": 0.8}
        hip = {"x": 0.5, "y": 0.8}
        angle = calculate_trunk_lean(shoulder, hip, coordinate_system="image")
        assert pytest.approx(angle, abs=1e-3) == 90.0

    def test_femur_angle_horizontal(self):
        # Đùi nằm ngang (y bằng nhau)
        hip = {"x": 0.4, "y": 0.7}
        knee = {"x": 0.7, "y": 0.7}
        angle = calculate_femur_angle(hip, knee, coordinate_system="image")
        assert pytest.approx(angle, abs=1e-3) == 0.0

    def test_knee_over_toe(self):
        # Đầu gối nhô quá mũi chân 50 pixels
        knee = {"x": 0.60, "y": 0.7}
        toe = {"x": 0.55, "y": 0.8}
        diff = calculate_knee_over_toe(knee, toe, width=1000.0)
        assert pytest.approx(diff, abs=1e-3) == 50.0

    def test_heel_rise(self):
        # Lúc setup gót chân ở y=0.85, lúc đáy nhấc lên y=0.80 (nhấc 50px với chiều cao 1000px)
        rise = calculate_heel_rise(heel_setup_y=0.85, heel_current_y=0.80, height=1000.0)
        assert pytest.approx(rise, abs=1e-3) == 50.0

        # Gót chân không nhấc hoặc ấn sâu hơn sàn -> trả về 0
        rise_zero = calculate_heel_rise(heel_setup_y=0.85, heel_current_y=0.86, height=1000.0)
        assert rise_zero == 0.0


class TestDominantSideDetection:
    """Kiểm tra tự động phát hiện hướng người tập quay vào camera."""

    class MockFrame:
        def __init__(self, is_detected: bool, l_vis: float, r_vis: float):
            self.is_detected = is_detected
            self.l_vis = l_vis
            self.r_vis = r_vis

        def get_landmark(self, name: str):
            if name.startswith("left_"):
                return {"visibility": self.l_vis}
            if name.startswith("right_"):
                return {"visibility": self.r_vis}
            return None

    def test_detect_right_dominant(self):
        frames = [self.MockFrame(True, l_vis=0.4, r_vis=0.9) for _ in range(10)]
        assert detect_dominant_side(frames) == "right"

    def test_detect_left_dominant(self):
        frames = [self.MockFrame(True, l_vis=0.9, r_vis=0.3) for _ in range(10)]
        assert detect_dominant_side(frames) == "left"


class TestSignalSmoothing:
    """Kiểm tra bộ lọc Savitzky-Golay và xử lý tín hiệu."""

    def test_smooth_removes_noise_preserves_minima(self):
        # Tạo hàm parabol y = (x - 50)^2 / 50 + 40 (đáy là 40 tại x=50)
        x = np.linspace(0, 100, 101)
        clean = (x - 50) ** 2 / 50 + 40
        np.random.seed(42)
        noise = np.random.normal(0, 3.0, size=len(x))
        noisy_signal = clean + noise

        smoothed = smooth_signal_1d(noisy_signal, window_length=15, polyorder=2)

        # Kiểm tra độ lệch chuẩn của sai số giảm đáng kể sau khi lọc
        raw_rmse = np.sqrt(np.mean((noisy_signal - clean) ** 2))
        smooth_rmse = np.sqrt(np.mean((smoothed - clean) ** 2))
        assert smooth_rmse < raw_rmse * 0.5

        # Đáy thật là 40, đáy sau lọc phải rất sát (với độ lệch chuẩn nhiễu 3.0, lệch < 2.0)
        assert abs(np.min(smoothed) - 40.0) < 2.0

    def test_smooth_handles_nans(self):
        signal = np.array([10.0, 20.0, np.nan, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0, 110.0])
        smoothed = smooth_signal_1d(signal, window_length=5, polyorder=2)
        assert not np.any(np.isnan(smoothed))
        assert len(smoothed) == len(signal)

    def test_short_series_no_crash(self):
        # Chuỗi rất ngắn
        short = np.array([10.0, 20.0, 30.0])
        smoothed = smooth_signal_1d(short, window_length=11, polyorder=2)
        assert len(smoothed) == 3

    def test_moving_average_blunts_extreme_minima(self):
        # Chứng minh Moving Average làm bẹt đáy so với Savitzky-Golay
        # Tạo đáy nhọn tại x=10
        x = np.array([100, 80, 60, 40, 20, 0, 20, 40, 60, 80, 100], dtype=float)
        savgol = smooth_signal_1d(x, window_length=5, polyorder=2)
        ma = moving_average_1d(x, window_size=5)

        # MA tại điểm đáy (x=0) sẽ bị kéo lên cao bởi các điểm lân cận
        assert np.min(ma) > np.min(savgol)
