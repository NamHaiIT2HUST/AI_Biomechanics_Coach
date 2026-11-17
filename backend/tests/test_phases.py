import numpy as np
import pytest
from app.core.phases import SquatPhase, segment_squat_reps


def rep(low=80, descend=20, ascend=20):
    return np.r_[np.linspace(170, low, descend, endpoint=False), np.linspace(low, 170, ascend + 1)]


def test_three_complete_reps_and_phase_timing():
    signal = np.r_[np.full(5, 170.), rep(), np.full(5, 170.), rep(90), np.full(5, 170.), rep(85), np.full(5, 170.)]
    hips = np.full(len(signal), 170.)
    trunk = np.arange(len(signal), dtype=float)
    reps, phases = segment_squat_reps(signal, 30, hip_angles=hips, trunk_lean=trunk)
    assert len(reps) == 3
    assert [r.rep_id for r in reps] == [1, 2, 3]
    for r in reps:
        assert r.start_frame < r.bottom_frame < r.end_frame
        assert r.total_duration_s >= 1
        assert r.eccentric_duration_s + r.concentric_duration_s == pytest.approx(r.total_duration_s)
        assert r.trunk_lean_at_bottom == trunk[r.bottom_frame]
        assert r.max_trunk_lean == trunk[r.end_frame]
        assert phases[r.bottom_frame] == SquatPhase.BOTTOM
        assert phases[r.end_frame] == SquatPhase.LOCKOUT
        assert r.max_heel_rise_px is None
    assert SquatPhase.ECCENTRIC in phases and SquatPhase.CONCENTRIC in phases


def test_shallow_and_incomplete_movements_not_counted():
    signal = np.r_[np.full(10, 170.), rep(120), np.full(10, 170.), np.linspace(170, 80, 40)]
    assert segment_squat_reps(signal, 30)[0] == []


def test_fast_movement_rejected():
    signal = np.r_[np.full(5, 170.), rep(80, 8, 8), np.full(5, 170.)]
    assert segment_squat_reps(signal, 30)[0] == []


def test_pause_and_missing_optional_values():
    signal = np.r_[np.full(4, 170.), np.linspace(170, 80, 20, endpoint=False), np.full(8, 80.), np.linspace(80, 170, 21), np.full(4, 170.)]
    trunk = np.full(len(signal), np.nan)
    reps, phases = segment_squat_reps(signal, 30, trunk_lean=trunk)
    assert len(reps) == 1
    assert reps[0].pause_duration_s >= 7 / 30
    assert reps[0].max_trunk_lean is None and reps[0].trunk_lean_at_bottom is None
    assert phases[reps[0].bottom_frame] == SquatPhase.BOTTOM


def test_missing_hip_does_not_invent_lockout():
    signal = np.r_[np.full(5, 170.), rep(), np.full(5, 170.)]
    reps, phases = segment_squat_reps(signal, 30)
    assert len(reps) == 1 and SquatPhase.LOCKOUT not in phases


@pytest.mark.parametrize('signal,fps', [([170, np.nan, 90], 30), ([170], 0), ([[170]], 30)])
def test_invalid_input_rejected(signal, fps):
    with pytest.raises(ValueError):
        segment_squat_reps(signal, fps)


def test_optional_signal_length_must_match():
    with pytest.raises(ValueError):
        segment_squat_reps([170, 90, 170], 30, hip_angles=[170])
