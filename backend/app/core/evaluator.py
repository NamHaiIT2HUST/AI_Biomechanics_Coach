"""Evaluate configured squat measurements without inventing missing findings.

Thresholds are experimental; results are not clinical assessments.
"""
import math
from numbers import Real
from typing import Any

METRICS = {'knee_at_bottom': 'min_knee_angle', 'trunk_at_bottom': 'trunk_lean_at_bottom'}
OPERATORS = {'>': lambda x, y: x > y, '>=': lambda x, y: x >= y,
             '<': lambda x, y: x < y, '<=': lambda x, y: x <= y}


def evaluate_squat(rep: dict[str, Any], config: dict[str, Any], *, camera_view: str) -> dict[str, Any]:
    """Assess one rep; low-confidence/unknown inputs never produce a pass or fault.

    camera_view is user-supplied, not verified by this function. The accepted
    side view enables projected 2D measurements only.
    """
    if config.get('id') != 'squat' or not isinstance(config.get('rules'), list):
        raise ValueError('Expected squat config with rules')
    if camera_view not in ('side_90deg', 'front_0deg', 'unknown'):
        raise ValueError('Invalid camera view')
    frame = rep.get('bottom_frame')
    if isinstance(frame, bool) or not isinstance(frame, int) or frame < 0:
        raise ValueError('bottom_frame must be a nonnegative integer')
    results = []
    seen = set()
    for rule in config['rules']:
        rule_id = rule.get('id')
        if not isinstance(rule_id, str) or not rule_id or rule_id in seen:
            raise ValueError('Invalid or duplicate rule ID')
        seen.add(rule_id)
        condition = rule.get('condition', {})
        metric, op, threshold = condition.get('metric'), condition.get('operator'), condition.get('threshold')
        if metric not in METRICS or op not in OPERATORS:
            raise ValueError(f'Unsupported rule: {rule_id}')
        if isinstance(threshold, bool) or not isinstance(threshold, Real) or not math.isfinite(threshold):
            raise ValueError(f'Invalid threshold: {rule_id}')
        result = {'rule_id': rule_id, 'name': rule.get('name'), 'metric': metric,
                  'benchmark_value': float(threshold), 'operator': op, 'unit': rule.get('unit'),
                  'evidence_frame': frame, 'measured_value': None, 'status': 'insufficient_data',
                  'reason': None}
        value = rep.get(METRICS[metric])
        if camera_view != 'side_90deg':
            result['reason'] = 'unsupported_camera_view'
        elif rep.get('quality_status') != 'no_low_visibility_detected':
            result['reason'] = 'pose_quality_not_sufficient'
        elif isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value) or not 0 <= value <= 180:
            result['reason'] = 'measurement_missing_or_invalid'
        else:
            result['measured_value'] = float(value)
            result['status'] = 'finding' if OPERATORS[op](value, threshold) else 'within_threshold'
        results.append(result)
    return {'rep_id': rep.get('rep_id'), 'camera_view': camera_view,
            'view_verification': 'user_supplied_unverified', 'rules': results,
            'warning': 'Thresholds are experimental and not medical diagnoses.'}


def evaluate_squat_analysis(analysis: dict[str, Any], config: dict[str, Any], *, camera_view: str) -> dict[str, Any]:
    """Assess detected reps and retain whether video coverage is incomplete."""
    if analysis.get('status') not in ('complete', 'partial') or not isinstance(analysis.get('reps'), list):
        raise ValueError('Expected a complete or partial landmark analysis')
    assessments = [evaluate_squat(rep, config, camera_view=camera_view) for rep in analysis['reps']]
    return {'analysis_status': analysis['status'], 'video_warning': analysis.get('warning'),
            'camera_view': camera_view, 'reps': assessments,
            'warning': 'Thresholds are experimental; camera angle is user-supplied and not verified.'}
