"""Unit tests for the Observation domain status machine — no DB needed."""
import pytest
from app.domain.observation import (
    Observation as ObsDomain,
    ObservationStatus,
    DomainError,
    VALID_TRANSITIONS,
)


def _make_obs(status=ObservationStatus.DRAFT):
    return ObsDomain(
        id="test-id", school_id="s1", teacher_id="t1",
        subject="Matemática", grade="5º ano",
        lesson_theme="Frações", lesson_objectives="",
        status=status, created_by="user1",
    )


def test_draft_to_ready_to_record():
    obs = _make_obs(ObservationStatus.DRAFT)
    obs.transition_to(ObservationStatus.READY_TO_RECORD)
    assert obs.status == ObservationStatus.READY_TO_RECORD


def test_draft_to_approved_raises():
    obs = _make_obs(ObservationStatus.DRAFT)
    with pytest.raises(DomainError, match="Invalid transition"):
        obs.transition_to(ObservationStatus.APPROVED)


def test_draft_to_transcribing_raises():
    obs = _make_obs(ObservationStatus.DRAFT)
    with pytest.raises(DomainError):
        obs.transition_to(ObservationStatus.TRANSCRIBING)


def test_all_defined_statuses_have_transitions():
    for status in ObservationStatus:
        assert status in VALID_TRANSITIONS, f"{status} not in VALID_TRANSITIONS"


def test_approved_has_no_further_transitions():
    obs = _make_obs(ObservationStatus.APPROVED)
    for status in ObservationStatus:
        if status != ObservationStatus.APPROVED:
            with pytest.raises(DomainError):
                obs.transition_to(status)


def test_is_ready_for_recording_true():
    obs = _make_obs(ObservationStatus.DRAFT)
    assert obs.is_ready_for_recording() is True


def test_is_ready_for_recording_false_when_theme_empty():
    obs = ObsDomain(
        id="test", school_id="s1", teacher_id="t1",
        subject="Matemática", grade="5º ano",
        lesson_theme="",  # empty
        lesson_objectives="", status=ObservationStatus.DRAFT, created_by="u1",
    )
    assert obs.is_ready_for_recording() is False
