import pytest
from app.core.rep_validation import evaluate_dataset, evaluate_video


def test_matches_are_one_to_one_with_false_positive_and_negative():
    result = evaluate_video([10, 50, 90], [11, 12, 90], 30, 0.1)
    assert (result["true_positives"], result["false_positives"], result["false_negatives"]) == (2, 1, 1)
    assert result["count_absolute_error"] == 0


def test_matching_maximizes_count_before_error():
    result = evaluate_video([10, 13], [12, 15], 10, 0.2)
    assert result["true_positives"] == 2


def test_empty_denominators_are_not_reported_as_perfect():
    result = evaluate_dataset([dict(id="a", fps=30, reference_bottom_frames=[], predicted_bottom_frames=[])])
    assert result["summary"]["precision"] is None
    assert result["summary"]["recall"] is None
    assert result["summary"]["mean_bottom_error_s"] is None


@pytest.mark.parametrize("values", [[1, 1], [-1], [1.1], [True]])
def test_invalid_frame_labels_rejected(values):
    with pytest.raises(ValueError):
        evaluate_video(values, [], 30)
