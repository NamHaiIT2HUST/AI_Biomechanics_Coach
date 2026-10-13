"""Module core bóc tách khung xương (Pose Estimation) sử dụng MediaPipe Pose Landmarker."""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# 33 khớp mốc chuẩn của MediaPipe Pose
POSE_CONNECTIONS = [
    # Thân trên & Cánh tay
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    # Thân mình (Cột sống / Khung xương chậu)
    (11, 23), (12, 24), (23, 24),
    # Chi dưới chân trái
    (23, 25), (25, 27), (27, 29), (29, 31), (27, 31),
    # Chi dưới chân phải
    (24, 26), (26, 28), (28, 30), (30, 32), (28, 32)
]

LANDMARK_NAMES = [
    "nose", "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer",
    "left_ear", "right_ear", "mouth_left", "mouth_right",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_pinky", "right_pinky",
    "left_index", "right_index", "left_thumb", "right_thumb",
    "left_hip", "right_hip", "left_knee", "right_knee",
    "left_ankle", "right_ankle", "left_heel", "right_heel",
    "left_foot_index", "right_foot_index"
]

@dataclass
class LandmarkPoint:
    id: int
    name: str
    x: float
    y: float
    z: float
    visibility: float
    presence: float

@dataclass
class FramePose:
    frame_idx: int
    timestamp_ms: float
    is_detected: bool
    landmarks: List[Dict[str, Any]]
    world_landmarks: List[Dict[str, Any]]

    def get_landmark(self, name_or_idx: Any) -> Optional[Dict[str, Any]]:
        """Lấy tọa độ khớp theo tên hoặc index."""
        if not self.is_detected:
            return None
        if isinstance(name_or_idx, int) and 0 <= name_or_idx < len(self.landmarks):
            return self.landmarks[name_or_idx]
        if isinstance(name_or_idx, str):
            for lm in self.landmarks:
                if lm["name"] == name_or_idx:
                    return lm
        return None

@dataclass
class VideoExtractionResult:
    video_path: str
    fps: float
    width: int
    height: int
    total_frames: int
    duration_s: float
    detected_frames_count: int
    detection_rate: float
    frames: List[FramePose]

class PoseEngine:
    """Lõi xử lý trích xuất tư thế người từ Video và Ảnh."""

    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            # Mặc định lấy model nặng trong ai/models/pretrained/
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            model_path = str(base_dir / "ai" / "models" / "pretrained" / "pose_landmarker_heavy.task")

        self.model_path = model_path
        if not Path(model_path).exists():
            raise FileNotFoundError(f"Không tìm thấy file mô hình MediaPipe tại: {model_path}")

        self.base_options = python.BaseOptions(model_asset_path=self.model_path)

    def extract_from_video(
        self,
        video_path: str,
        max_frames: Optional[int] = None,
        progress_callback: Optional[Any] = None
    ) -> VideoExtractionResult:
        """Trích xuất chuỗi 33 khớp từ file video MP4/MOV."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Không thể mở file video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration_s = total_frames / fps if fps > 0 else 0.0

        options = vision.PoseLandmarkerOptions(
            base_options=self.base_options,
            running_mode=vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )

        detector = vision.PoseLandmarker.create_from_options(options)
        frames_data: List[FramePose] = []
        detected_count = 0
        frame_idx = 0

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if max_frames and frame_idx >= max_frames:
                    break

                # MediaPipe yêu cầu RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

                timestamp_ms = int((frame_idx / fps) * 1000)
                detection_result = detector.detect_for_video(mp_image, timestamp_ms)

                is_detected = bool(detection_result.pose_landmarks and len(detection_result.pose_landmarks) > 0)
                landmarks_list: List[Dict[str, Any]] = []
                world_landmarks_list: List[Dict[str, Any]] = []

                if is_detected:
                    detected_count += 1
                    raw_landmarks = detection_result.pose_landmarks[0]
                    raw_world = detection_result.pose_world_landmarks[0]

                    for idx, (lm, wlm) in enumerate(zip(raw_landmarks, raw_world)):
                        name = LANDMARK_NAMES[idx] if idx < len(LANDMARK_NAMES) else f"joint_{idx}"
                        landmarks_list.append({
                            "id": idx,
                            "name": name,
                            "x": float(lm.x),
                            "y": float(lm.y),
                            "z": float(lm.z),
                            "visibility": float(getattr(lm, "visibility", 1.0)),
                            "presence": float(getattr(lm, "presence", 1.0))
                        })
                        world_landmarks_list.append({
                            "id": idx,
                            "name": name,
                            "x": float(wlm.x),
                            "y": float(wlm.y),
                            "z": float(wlm.z),
                            "visibility": float(getattr(wlm, "visibility", 1.0)),
                            "presence": float(getattr(wlm, "presence", 1.0))
                        })

                frames_data.append(FramePose(
                    frame_idx=frame_idx,
                    timestamp_ms=float(timestamp_ms),
                    is_detected=is_detected,
                    landmarks=landmarks_list,
                    world_landmarks=world_landmarks_list
                ))

                frame_idx += 1
                if progress_callback and total_frames > 0:
                    progress_callback(frame_idx, total_frames)

        finally:
            cap.release()
            detector.close()

        detection_rate = (detected_count / frame_idx) if frame_idx > 0 else 0.0

        return VideoExtractionResult(
            video_path=video_path,
            fps=float(fps),
            width=width,
            height=height,
            total_frames=frame_idx,
            duration_s=float(duration_s),
            detected_frames_count=detected_count,
            detection_rate=float(detection_rate),
            frames=frames_data
        )

    @staticmethod
    def draw_skeleton(
        image: np.ndarray,
        landmarks: List[Dict[str, Any]],
        color_bones: Tuple[int, int, int] = (0, 255, 128),  # Xanh ngọc
        color_joints: Tuple[int, int, int] = (255, 255, 255), # Trắng
        thickness: int = 2,
        radius: int = 4
    ) -> np.ndarray:
        """Vẽ khung xương và các khớp lên ảnh BGR."""
        h, w, _ = image.shape
        img_copy = image.copy()

        # Tạo dict map idx -> (px, py)
        points: Dict[int, Tuple[int, int]] = {}
        for lm in landmarks:
            if lm["visibility"] > 0.4:
                px = int(lm["x"] * w)
                py = int(lm["y"] * h)
                points[lm["id"]] = (px, py)

        # Vẽ xương nối
        for start_idx, end_idx in POSE_CONNECTIONS:
            if start_idx in points and end_idx in points:
                cv2.line(img_copy, points[start_idx], points[end_idx], color_bones, thickness, cv2.LINE_AA)

        # Vẽ các điểm khớp
        for idx, (px, py) in points.items():
            cv2.circle(img_copy, (px, py), radius, color_joints, -1, cv2.LINE_AA)
            cv2.circle(img_copy, (px, py), radius + 1, (0, 140, 255), 1, cv2.LINE_AA)

        return img_copy
