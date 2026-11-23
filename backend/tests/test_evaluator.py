import json
from pathlib import Path
import pytest
from app.core.evaluator import evaluate_squat

CONFIG = json.loads((Path(__file__).resolve().parents[1] / 'app/exercises/squat.json').read_text(encoding='utf8'))


def rep(**overrides):
    value = {'rep_id': 1, 'bottom_frame': 40, 'min_knee_angle': 120.0, 'trunk_lean_at_bottom': 50.0,
             'quality_status': 'no_low_visibility_detected'}
    return value | overrides


def test_side_view_produces_findings_with_source_measurements():
    result = evaluate_squat(rep(), CONFIG, camera_view='side_90deg')
    assert [r['status'] for r in result['rules']] == ['finding', 'finding']
    assert result['rules'][0]['measured_value'] == 120 and result['rules'][0]['evidence_frame'] == 40
    assert result['view_verification'] == 'user_supplied_unverified'


def test_within_threshold_and_missing_measurement_are_distinct():
    result = evaluate_squat(rep(min_knee_angle=90, trunk_lean_at_bottom=None), CONFIG, camera_view='side_90deg')
    assert result['rules'][0]['status'] == 'within_threshold'
    assert result['rules'][1]['status'] == 'insufficient_data'


def test_low_confidence_and_wrong_view_never_produce_findings():
    result = evaluate_squat(rep(quality_status='needs_review'), CONFIG, camera_view='side_90deg')
    assert {r['reason'] for r in result['rules']} == {'pose_quality_not_sufficient'}
    result = evaluate_squat(rep(), CONFIG, camera_view='front_0deg')
    assert {r['reason'] for r in result['rules']} == {'unsupported_camera_view'}


def test_rule_labels_are_measurements_not_universal_technique_judgments():
    result = evaluate_squat(rep(), CONFIG, camera_view='side_90deg')
    assert [r['name'] for r in result['rules']] == ['Góc gối tại đáy', 'Độ ngả thân tại đáy']


def test_invalid_rule_config_fails_closed():
    with pytest.raises(ValueError, match='Unsupported'):
        evaluate_squat(rep(), {'id': 'squat', 'rules': [{'id': 'x', 'condition': {'metric': 'made_up', 'operator': '>', 'threshold': 1}}]}, camera_view='side_90deg')


def test_partial_video_status_is_preserved_without_inventing_missing_reps():
    from app.core.evaluator import evaluate_squat_analysis
    result = evaluate_squat_analysis({'status': 'partial', 'warning': 'missing pose', 'reps': [rep()]}, CONFIG, camera_view='side_90deg')
    assert result['analysis_status'] == 'partial'
    assert result['video_warning'] == 'missing pose'
    assert len(result['reps']) == 1
