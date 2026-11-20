"""Analyze uninterrupted pose spans without fabricating missing observations."""
from copy import deepcopy
from typing import Any

import numpy as np
from app.core.landmark_analysis import analyze_landmarks


def analyze_detected_spans(data: dict[str, Any], *, min_duration_s: float = 1.0,
                           min_visibility: float = 0.5, bottom_threshold: float = 150.0):
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
    side = data.get('dominant_side')
    if side is None:
        scores = {}
        for candidate in ('left', 'right'):
            values = []
            for frame in frames:
                points = {p.get('name'): p for p in frame.get('landmarks', [])}
                values.extend(float(points.get(candidate + '_' + name, {}).get('visibility', 0))
                              for name in ('shoulder', 'hip', 'knee', 'ankle'))
            scores[candidate] = float(np.mean(values))
        side = max(scores, key=scores.get)
    if side not in ('left', 'right'):
        raise ValueError('Invalid dominant side')
    required = {side + '_' + name for name in ('shoulder', 'hip', 'knee', 'ankle')}
    good = [bool(f.get('is_detected')) and required.issubset({p.get('name') for p in f.get('landmarks', [])}) for f in frames]
    spans = []
    start = None
    for index, valid in enumerate(good + [False]):
        if valid and start is None:
            start = index
        elif not valid and start is not None:
            spans.append((start, index))
            start = None
    reps, analysed, warnings = [], 0, []
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
                                   min_visibility=min_visibility, bottom_threshold=bottom_threshold)
        analysed += end - start
        for rep in result['reps']:
            item = deepcopy(rep)
            item['rep_id'] = len(reps) + 1
            for name in ('start_frame', 'bottom_frame', 'end_frame'):
                item[name] += start
            for name in ('start_time_s', 'bottom_time_s', 'end_time_s'):
                item[name] += start / fps
            reps.append(item)
    missing = len(frames) - sum(good)
    return {'status': 'complete' if not missing and analysed == len(frames) else 'partial',
            'dominant_side': side, 'total_frames': len(frames), 'missing_frames': missing,
            'analyzed_frames': analysed, 'spans': [{'start_frame': a, 'end_frame': b - 1} for a, b in spans],
            'warnings': warnings, 'reps': reps,
            'warning': 'Partial: reps crossing missing pose frames may be missed; count is not complete.'
            if missing or analysed != len(frames) else 'Detection and quality remain unvalidated.'}
