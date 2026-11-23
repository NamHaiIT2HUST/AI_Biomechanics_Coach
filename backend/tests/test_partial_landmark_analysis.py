import numpy as np
import pytest
from app.core.partial_landmark_analysis import analyze_detected_spans


def make_data(angles, missing=()):
    frames = []
    for i, angle in enumerate(angles):
        r = np.radians(angle)
        hx, hy = 0.5 + 0.2 * np.sin(r), 0.5 + 0.2 * np.cos(r)
        joints = {'shoulder': (hx, hy - 0.2), 'hip': (hx, hy), 'knee': (.5, .5), 'ankle': (.5, .7)}
        lms = [dict(name='right_' + name, x=x, y=y, visibility=.9) for name, (x, y) in joints.items()]
        frames.append(dict(frame_idx=i, is_detected=i not in missing, landmarks=[] if i in missing else lms))
    return {'fps': 30, 'width': 1000, 'height': 1000, 'dominant_side': 'right', 'frames': frames}


def test_missing_pose_breaks_spans_preserves_global_frames():
    rep = np.r_[np.linspace(170, 80, 20, endpoint=False), np.linspace(80, 170, 21)]
    angles = np.r_[np.full(10, 170), rep, np.full(10, 170)]
    result = analyze_detected_spans(make_data(angles, missing=(2,)))
    assert result['status'] == 'partial'
    assert result['missing_frames'] == 1
    assert len(result['reps']) == 1
    assert result['reps'][0]['bottom_frame'] == 30
    assert result['reps'][0]['bottom_time_s'] == pytest.approx(1.0)


def test_gap_inside_rep_does_not_fabricate_a_complete_rep():
    rep = np.r_[np.linspace(170, 80, 20, endpoint=False), np.linspace(80, 170, 21)]
    angles = np.r_[np.full(10, 170), rep, np.full(10, 170)]
    result = analyze_detected_spans(make_data(angles, missing=(30,)))
    assert result['status'] == 'partial'
    assert result['reps'] == []
    assert 'not complete' in result['warning']


def test_no_detected_frames_reports_partial():
    result = analyze_detected_spans(make_data([170] * 20, missing=range(20)))
    assert result['status'] == 'partial'
    assert result['analyzed_frames'] == 0
    assert result['reps'] == []


def test_noncontinuous_frames_rejected():
    data = make_data([170] * 10)
    data['frames'][5]['frame_idx'] = 7
    with pytest.raises(ValueError, match='continuously'):
        analyze_detected_spans(data)
from app.core.landmark_analysis import analyze_landmarks


def test_no_missing_frames_matches_existing_strict_analyzer():
    rep = np.r_[np.linspace(170, 80, 20, endpoint=False), np.linspace(80, 170, 21)]
    data = make_data(np.r_[np.full(10, 170), rep, np.full(10, 170)])
    strict = analyze_landmarks(data)
    partial = analyze_detected_spans(data)
    assert partial['status'] == 'complete'
    assert partial['reps'] == strict['reps']


def test_missing_pose_near_rep_blocks_confident_evaluation():
    rep = np.r_[np.linspace(170, 80, 20, endpoint=False), np.linspace(80, 170, 21)]
    angles = np.r_[np.full(10, 170), rep, np.full(10, 170)]
    result = analyze_detected_spans(make_data(angles, missing=(7,)))
    assert len(result['reps']) == 1
    assert result['reps'][0]['missing_pose_near_rep'] is True
    assert result['reps'][0]['quality_status'] == 'needs_review'


@pytest.mark.parametrize('invalid', ['coincident', 'nan', 'bad_visibility'])
def test_invalid_geometry_splits_span_instead_of_fabricating_angles(invalid):
    rep = np.r_[np.linspace(170, 80, 20, endpoint=False), np.linspace(80, 170, 21)]
    data = make_data(np.r_[np.full(10, 170), rep, np.full(10, 170)])
    points = {p['name']: p for p in data['frames'][30]['landmarks']}
    if invalid == 'coincident':
        points['right_hip']['x'] = points['right_knee']['x']
        points['right_hip']['y'] = points['right_knee']['y']
    elif invalid == 'nan':
        points['right_knee']['x'] = float('nan')
    else:
        points['right_knee']['visibility'] = 2
    result = analyze_detected_spans(data)
    assert result['status'] == 'partial'
    assert result['missing_frames'] == 1
    assert result['reps'] == []


def test_low_visibility_count_is_reported_even_without_reps():
    data = make_data([170] * 20)
    data['frames'][4]['landmarks'][0]['visibility'] = .1
    result = analyze_detected_spans(data)
    assert result['reps'] == []
    assert result['low_visibility_frames'] == 1
