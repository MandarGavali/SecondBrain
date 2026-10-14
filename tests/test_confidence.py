from secondbrain.verification.confidence import (
    compute_confidence, decide, label_for, strip_verbal_confidence,
)


def test_grounded_high_scores_is_high():
    assert compute_confidence([0.9, 0.8, 0.7], True) > 0.8


def test_ungrounded_lowers_confidence():
    assert compute_confidence([0.9], False) < compute_confidence([0.9], True)


def test_missing_grounding_renormalises():
    assert 0.0 < compute_confidence([0.8, 0.6], None) <= 1.0


def test_no_scores_is_zero_without_grounding():
    assert compute_confidence([], None) == 0.0


def test_labels():
    assert label_for(0.8) == "High"
    assert label_for(0.5) == "Medium"
    assert label_for(0.1) == "Low"


def test_decide_paths():
    assert decide(True, 0.9, 0) == "deliver"
    assert decide(False, 0.9, 0) == "retry"
    assert decide(False, 0.9, 1) == "abstain"
    assert decide(True, 0.05, 0) == "retry"


def test_strip_verbal_confidence():
    assert strip_verbal_confidence("Answer text\n\nConfidence:\nHigh") == "Answer text"
    assert strip_verbal_confidence("Answer text\n**Confidence:** Medium") == "Answer text"
    assert strip_verbal_confidence("No marker here") == "No marker here"
