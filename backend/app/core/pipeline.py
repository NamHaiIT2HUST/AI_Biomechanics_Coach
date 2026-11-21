"""Video-to-squat-assessment pipeline for the local MVP.

Results are experimental and the supplied camera view is not verified.
"""
import argparse
from dataclasses import asdict
import hashlib
import json
import math
from numbers import Real
from pathlib import Path

from app.config import settings
from app.core.evaluator import evaluate_squat, evaluate_squat_analysis
from app.core.partial_landmark_analysis import analyze_detected_spans
from app.core.pose import PoseEngine


def load_squat_config(path=None):
    config_path = Path(path) if path is not None else settings.EXERCISES_CONFIG_DIR / 'squat.json'
    config = json.loads(config_path.read_text(encoding='utf8'))
    return config


def _parameters(config):
    if config.get('id') != 'squat':
        raise ValueError('Only squat is supported')
    counter = config.get('rep_counter', {})
    values = {
        'bottom_threshold': counter.get('enter_bottom_threshold'),
        'standing_threshold': counter.get('exit_top_threshold'),
        'min_duration_s': counter.get('min_duration_s'),
        'min_visibility': counter.get('min_visibility'),
        'prominence': config.get('phases', {}).get('bottom', {}).get('prominence'),
    }
    for name, value in values.items():
        if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
            raise ValueError(f'Invalid squat config value: {name}')
    if not 0 <= values['bottom_threshold'] < values['standing_threshold'] <= 180:
        raise ValueError('Invalid squat detection thresholds')
    if values['min_duration_s'] <= 0 or values['prominence'] <= 0 or not 0 <= values['min_visibility'] <= 1:
        raise ValueError('Invalid squat segmentation/visibility parameters')
    # Validate rules even if video has no detected reps.
    if not isinstance(config.get('rules'), list) or not config['rules']:
        raise ValueError('Squat config must define at least one rule')
    evaluate_squat({'bottom_frame': 0}, config, camera_view='unknown')
    return values


def analyze_squat_video(video_path, *, camera_view, config=None, engine=None):
    """Run pose → kinematics → segmentation → evaluator on one local video.

    Does not store the video or output automatically; an injected engine can be
    used for integration testing. Frame times use nominal constant video FPS.
    """
    video = Path(video_path)
    if not video.is_file():
        raise FileNotFoundError(f'Video not found: {video}')
    if camera_view not in ('side_90deg', 'front_0deg', 'unknown'):
        raise ValueError('Invalid camera view')
    config = config if config is not None else load_squat_config()
    params = _parameters(config)
    engine = engine if engine is not None else PoseEngine()
    extraction = engine.extract_from_video(str(video))
    pose = asdict(extraction)
    if not pose['frames'] or extraction.total_frames != len(pose['frames']):
        raise ValueError('No usable decoded frames or inconsistent extraction metadata')
    analysis = analyze_detected_spans(pose, **params)
    evaluation = evaluate_squat_analysis(analysis, config, camera_view=camera_view)
    evaluations = {item['rep_id']: item for item in evaluation['reps']}
    reps = []
    for rep in analysis['reps']:
        entry = dict(rep)
        entry['assessment'] = evaluations[rep['rep_id']]['rules']
        reps.append(entry)
    warnings = [analysis['warning'], evaluation['warning']]
    if camera_view != 'side_90deg':
        warnings.append('Side-view metrics are unavailable for the supplied camera view.')
    min_fps = config.get('camera', {}).get('min_fps')
    if isinstance(min_fps, Real) and not isinstance(min_fps, bool) and extraction.fps < min_fps:
        warnings.append(f'Video FPS is below the configured recommendation of {min_fps}.')
    if not analysis['analyzed_frames']:
        outcome = 'insufficient_data'
    elif not reps:
        outcome = 'no_reps_detected'
    else:
        outcome = 'reps_detected'
    canonical_config = json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf8')
    return {
        'schema_version': '1.0', 'exercise_id': 'squat', 'outcome': outcome,
        'video': {'filename': video.name, 'fps': extraction.fps, 'width': extraction.width,
                  'height': extraction.height, 'decoded_frames': extraction.total_frames,
                  'duration_s': extraction.total_frames / extraction.fps,
                  'camera_view': camera_view, 'camera_view_verification': 'user_supplied_unverified'},
        'pose': {'detected_frames': extraction.detected_frames_count, 'detection_rate': extraction.detection_rate,
                 'dominant_side': analysis['dominant_side']},
        'coverage': {'status': analysis['status'], 'missing_frames': analysis['missing_frames'],
                     'analyzed_frames': analysis['analyzed_frames'], 'spans': analysis['spans'],
                     'warnings': analysis['warnings']},
        'config': {'sha256': hashlib.sha256(canonical_config).hexdigest(), 'parameters': params,
                   'experimental': True},
        'detected_rep_count': len(reps), 'reps': reps, 'warnings': warnings,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video', type=Path)
    parser.add_argument('--camera-view', required=True, choices=('side_90deg', 'front_0deg', 'unknown'))
    parser.add_argument('--config', type=Path)
    parser.add_argument('--output', type=Path, help='Write JSON to a new file; never overwrite')
    args = parser.parse_args()
    if args.output is not None and args.output.exists():
        parser.error('Output file already exists; choose a new path')
    result = analyze_squat_video(args.video, camera_view=args.camera_view, config=load_squat_config(args.config))
    payload = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    if args.output is None:
        print(payload)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf8') as file:
            file.write(payload + '\n')
        print(f'Analysis written to {args.output}')


if __name__ == '__main__':
    main()
