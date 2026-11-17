"""So sánh mốc đáy được dự đoán với nhãn thủ công độc lập.

JSON đầu vào: {"videos": [{"id": "...", "fps": 30,
 "reference_bottom_frames": [89, 133], "predicted_bottom_frames": [90, 133]}]}.
Các mốc phải được gán thủ công trước khi xem dự đoán. Chỉ so sánh các mốc được cung cấp.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment


def evaluate_video(reference, predicted, fps, tolerance_s=0.2):
    """Ghép 1-1 tối đa trong sai lệch cho phép rồi tối thiểu tổng sai lệch."""
    if not np.isfinite(fps) or fps <= 0 or not np.isfinite(tolerance_s) or tolerance_s < 0:
        raise ValueError("fps phải dương; tolerance_s không âm")
    def frames(values):
        if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in values):
            raise ValueError("Frame phải là số nguyên không âm")
        if len(set(values)) != len(values):
            raise ValueError("Không được lặp lại cùng frame đáy")
        return np.asarray(sorted(values), dtype=int)
    truth, pred = frames(reference), frames(predicted)
    matches = []
    if len(truth) and len(pred):
        delta = np.abs(truth[:, None] - pred[None, :]) / fps
        valid = delta <= tolerance_s + 1e-12
        # Dummy assignments let each truth remain unmatched; unmatched penalty is
        # greater than all possible total timing errors, so cardinality wins.
        penalty = (min(len(truth), len(pred)) + 1) * (tolerance_s + 1)
        cost = np.full((len(truth), len(pred) + len(truth)), penalty)
        cost[:, :len(pred)] = np.where(valid, delta, penalty * 2)
        rows, cols = linear_sum_assignment(cost)
        for r, c in zip(rows, cols):
            if c < len(pred) and valid[r, c]:
                matches.append({"reference_frame": int(truth[r]), "predicted_frame": int(pred[c]), "absolute_error_s": float(delta[r, c])})
    tp = len(matches)
    return {"reference_count": len(truth), "predicted_count": len(pred), "true_positives": tp,
            "false_positives": len(pred) - tp, "false_negatives": len(truth) - tp,
            "count_absolute_error": abs(len(pred) - len(truth)), "matches": matches}


def evaluate_dataset(videos, tolerance_s=0.2):
    ids = [v["id"] for v in videos]
    if len(ids) != len(set(ids)):
        raise ValueError("Mỗi video phải có id duy nhất")
    results = []
    for video in videos:
        result = evaluate_video(video["reference_bottom_frames"], video["predicted_bottom_frames"], float(video["fps"]), tolerance_s)
        results.append({"id": video["id"], **result})
    tp = sum(v["true_positives"] for v in results)
    fp = sum(v["false_positives"] for v in results)
    fn = sum(v["false_negatives"] for v in results)
    errors = [m["absolute_error_s"] for v in results for m in v["matches"]]
    return {"tolerance_s": tolerance_s, "videos": results, "summary": {
        "videos": len(results), "true_positives": tp, "false_positives": fp, "false_negatives": fn,
        "precision": tp / (tp + fp) if tp + fp else None,
        "recall": tp / (tp + fn) if tp + fn else None,
        "mean_bottom_error_s": float(np.mean(errors)) if errors else None,
        "mean_count_absolute_error": float(np.mean([v["count_absolute_error"] for v in results])) if results else None}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--tolerance", type=float, default=0.2)
    args = parser.parse_args()
    data = json.loads(args.path.read_text(encoding="utf8"))
    print(json.dumps(evaluate_dataset(data["videos"], args.tolerance), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
