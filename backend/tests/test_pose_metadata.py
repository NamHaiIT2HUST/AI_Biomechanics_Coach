import cv2
import pytest
from app.core.pose import PoseEngine


class FakeCapture:
    def __init__(self, fps):
        self.fps = fps
        self.released = False

    def isOpened(self):
        return True

    def get(self, property_id):
        return {cv2.CAP_PROP_FPS: self.fps, cv2.CAP_PROP_FRAME_WIDTH: 720,
                cv2.CAP_PROP_FRAME_HEIGHT: 1280, cv2.CAP_PROP_FRAME_COUNT: 100}[property_id]

    def release(self):
        self.released = True


@pytest.mark.parametrize('fps', [0.0, float('nan'), float('inf')])
def test_invalid_fps_is_not_silently_replaced(monkeypatch, fps):
    capture = FakeCapture(fps)
    monkeypatch.setattr(cv2, 'VideoCapture', lambda path: capture)
    engine = PoseEngine.__new__(PoseEngine)
    with pytest.raises(ValueError, match='invalid FPS'):
        engine.extract_from_video('video.mp4')
    assert capture.released
