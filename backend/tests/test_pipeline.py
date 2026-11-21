from copy import deepcopy
from dataclasses import dataclass
import json
from pathlib import Path
import numpy as np
import pytest
from app.core.pipeline import analyze_squat_video, load_squat_config


@dataclass
class FakeExtraction:
    fps: float
    width: int
    height: int
    total_frames: int
    detected_frames_count: int
    detection_rate: float
    frames: list


class FakeEngine:
    def __init__(self, missing=(), depth=120):
        self.missing = set(missing)
        self.depth = depth
        self.calls = 0

    def extract_from_video(self, path):
        self.calls += 1
        angles = np.r_[np.full(10, 170.), np.linspace(170, self.depth, 20, endpoint=False),
                       np.linspace(self.depth, 170, 21), np.full(10, 170.)]
        frames = []
        for i, angle in enumerate(angles):
            rad = np.radians(angle)
            hip = (.5 + .2 * np.sin(rad), .5 + .2 * np.cos(rad))
            joints = {'shoulder': (hip[0], hip[1] - .2), 'hip': hip,
                      'knee': (.5, .5), 'ankle': (.5, .7)}
            points = [dict(name='right_' + name, x=x, y=y, visibility=.9)
                      for name, (x, y) in joints.items()]
            frames.append(dict(frame_idx=i, is_detected=i not in self.missing,
                               landmarks=[] if i in self.missing else points))
        detected = len(frames) - len(self.missing)
        return FakeExtraction(30., 1000, 1000, len(frames), detected, detected / len(frames), frames)


def test_pipeline_connects_video_rep_and_configured_evaluation(tmp_path):
    video = tmp_path / 'source.mp4'
    video.write_bytes(b'stub')
    result = analyze_squat_video(video, camera_view='side_90deg', engine=FakeEngine())
    assert result['outcome'] == 'reps_detected'
    assert result['coverage']['status'] == 'complete'
    assert result['detected_rep_count'] == 1
    assert result['reps'][0]['assessment'][0]['status'] == 'finding'
    assert result['reps'][0]['assessment'][0]['evidence_frame'] == result['reps'][0]['bottom_frame']
    assert result['config']['parameters']['bottom_threshold'] == 150
    assert result['video']['camera_view_verification'] == 'user_supplied_unverified'
    json.dumps(result, allow_nan=False)


def test_configuration_changes_rep_detection_and_is_not_hardcoded(tmp_path):
    video = tmp_path / 'source.mp4'; video.write_bytes(b'stub')
    config = deepcopy(load_squat_config())
    config['rep_counter']['enter_bottom_threshold'] = 105
    result = analyze_squat_video(video, camera_view='side_90deg', engine=FakeEngine(), config=config)
    assert result['detected_rep_count'] == 0 and result['outcome'] == 'no_reps_detected'
    assert result['config']['parameters']['bottom_threshold'] == 105


def test_gap_and_wrong_camera_are_exposed(tmp_path):
    video = tmp_path / 'source.mp4'; video.write_bytes(b'stub')
    result = analyze_squat_video(video, camera_view='front_0deg', engine=FakeEngine(missing=(2,)))
    assert result['coverage']['status'] == 'partial'
    assert result['coverage']['missing_frames'] == 1
    assert result['reps'][0]['assessment'][0]['reason'] == 'unsupported_camera_view'
    assert 'not complete' in result['warnings'][0]


def test_missing_pose_is_insufficient_data_not_success(tmp_path):
    video = tmp_path / 'source.mp4'; video.write_bytes(b'stub')
    result = analyze_squat_video(video, camera_view='side_90deg', engine=FakeEngine(missing=range(61)))
    assert result['outcome'] == 'insufficient_data'
    assert result['detected_rep_count'] == 0


def test_invalid_config_rejected_before_running_pose(tmp_path):
    video = tmp_path / 'source.mp4'; video.write_bytes(b'stub')
    engine = FakeEngine()
    config = deepcopy(load_squat_config()); config['rep_counter']['enter_bottom_threshold'] = 180
    with pytest.raises(ValueError, match='threshold'):
        analyze_squat_video(video, camera_view='side_90deg', engine=engine, config=config)
    assert engine.calls == 0


def test_missing_video_rejected(tmp_path):
    with pytest.raises(FileNotFoundError):
        analyze_squat_video(tmp_path / 'missing.mp4', camera_view='side_90deg', engine=FakeEngine())


def test_empty_rules_are_rejected_even_if_no_reps(tmp_path):
    video = tmp_path / 'source.mp4'; video.write_bytes(b'stub')
    config = deepcopy(load_squat_config()); config['rules'] = []
    engine = FakeEngine()
    with pytest.raises(ValueError, match='at least one rule'):
        analyze_squat_video(video, camera_view='side_90deg', engine=engine, config=config)
    assert engine.calls == 0
