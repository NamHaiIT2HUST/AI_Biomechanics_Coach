"""Analyze uninterrupted pose spans without fabricating missing observations."""
from copy import deepcopy
from typing import Any

import numpy as np
from app.core.landmark_analysis import analyze_landmarks


def _usable_frame(frame, side, width, height):
    """Reject missing, malformed and geometrically undefined observations."""
    if not frame.get('is_detected'):
        return False
    points = {p.get('name'): p for p in frame.get('landmarks', []) if isinstance(p, dict)}
    coords = []
    try:
        for joint in ('shoulder', 'hip', 'knee', 'ankle'):
            point = points[side + '_' + joint]
            x, y = float(point['x']), float(point['y'])
            visibility = float(point.get('visibility', 0))
            if not np.isfinite([x, y, visibility]).all() or not 0 <= visibility <= 1:
                return False
            pixel = np.array([x * width, y * height])
            if not np.isfinite(pixel).all():
                return False
            coords.append(pixel)
    except (KeyError, TypeError, ValueError, OverflowError):
        return False
    # A zero-length limb cannot define a joint or trunk angle. Do not allow the
    # geometry helper's legacy 0° fallback to masquerade as a real measurement.
    return all(np.linalg.norm(a - b) >= 1e-7 for a, b in zip(coords, coords[1:]))


def analyze_detected_spans(data: dict[str, Any], *, min_duration_s: float = 1.0,
                           min_visibility: float = 0.5, bottom_threshold: float = 150.0,
                           standing_threshold: float = 160.0, prominence: float = 15.0):
    """Run the strict analyzer per contiguous span, retain original frame indices.

    Reps crossing gaps are not reconstructed. A result with gaps is explicitly
    partial and its detected count must not be presented as a complete count.
    Low-visibility detected landmarks retain the strict analyzer's warning.
    """
    frames = data['frames']
    if not frames or any(f.get('frame_idx') != i for i, f in enumerate(frames)):
        raise ValueError('Frames must be present and indexed continuously from zero')
    fps = float(data['fps'])
    if not np.isfinite(fps) or fps <= 0:
        raise ValueError('fps must be positive and finite')
    width, height = float(data['width']), float(data['height'])
    if not np.isfinite([width, height]).all() or width <= 0 or height <= 0:
        raise ValueError('width and height must be positive and finite')
    side = data.get('dominant_side')
    if side is None:
        scores = {}
        for candidate in ('left', 'right'):
            values = []
            for frame in frames:
                if not _usable_frame(frame, candidate, width, height):
                    values.extend([0.0] * 4)
                    continue
                points = {p.get('name'): p for p in frame.get('landmarks', []) if isinstance(p, dict)}
                values.extend(float(points[candidate + '_' + name].get('visibility', 0))
                              for name in ('shoulder', 'hip', 'knee', 'ankle'))
            scores[candidate] = float(np.mean(values)) if values else 0.0
        side = max(scores, key=scores.get)
    if side not in ('left', 'right'):
        raise ValueError('Invalid dominant side')
    good = [_usable_frame(f, side, width, height) for f in frames]
    spans = []
    start = None
    for index, valid in enumerate(good + [False]):
        if valid and start is None:
            start = index
        elif not valid and start is not None:
            spans.append((start, index))
            start = None
    reps, short_candidates, analysed, low_visibility_frames, warnings = [], [], 0, 0, []
    for start, end in spans:
        if end - start < 3:
            warnings.append({'start_frame': start, 'end_frame': end - 1, 'reason': 'span_too_short'})
            continue
        local = []
        for index in range(start, end):
            frame = dict(frames[index])
            frame['frame_idx'] = index - start
            local.append(frame)
        payload = dict(data, frames=local, dominant_side=side)
        result = analyze_landmarks(payload, min_duration_s=min_duration_s,
                                   min_visibility=min_visibility, bottom_threshold=bottom_threshold,
                                   standing_threshold=standing_threshold, prominence=prominence)
        analysed += end - start
        low_visibility_frames += result['low_visibility_frames']
        for candidate in result['short_motion_candidates']:
            item = dict(candidate)
            for name in ('start_frame', 'bottom_frame', 'end_frame'):
                item[name] += start
            item['bottom_time_s'] = item['bottom_frame'] / fps
            short_candidates.append(item)
        for rep in result['reps']:
            item = deepcopy(rep)
            item['rep_id'] = len(reps) + 1
            for name in ('start_frame', 'bottom_frame', 'end_frame'):
                item[name] += start
            for name in ('start_time_s', 'bottom_time_s', 'end_time_s'):
                item[name] += start / fps
            # The 11-frame smoother has a five-frame radius; a missing pose just
            # outside a span means the rep lacks full temporal context.
            near_gap = ((start > 0 and item['start_frame'] - start < 5) or
                        (end < len(frames) and end - 1 - item['end_frame'] < 5))
            if near_gap:
                item['quality_status'] = 'needs_review'
                item['missing_pose_near_rep'] = True
            reps.append(item)
    missing = len(frames) - sum(good)
    return {'status': 'complete' if not missing and analysed == len(frames) else 'partial',
            'dominant_side': side, 'total_frames': len(frames), 'missing_frames': missing,
            'analyzed_frames': analysed, 'low_visibility_frames': low_visibility_frames,
            'short_motion_candidates': short_candidates,
            'spans': [{'start_frame': a, 'end_frame': b - 1} for a, b in spans],
            'warnings': warnings, 'reps': reps,
            'warning': 'Partial: reps crossing missing pose frames may be missed; count is not complete.'
            if missing or analysed != len(frames) else 'Detection and quality remain unvalidated.'}
