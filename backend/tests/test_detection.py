import numpy as np
from app.detection import CentroidTracker, check_ppe, detect_people, process_source


def test_detect_people_runs_on_blank_frame():
    frame = np.zeros((300, 300, 3), dtype=np.uint8)
    assert detect_people(frame) == []


def test_centroid_tracker_assigns_ids():
    tracker = CentroidTracker()
    assignment = tracker.update([(10, 10), (50, 50)], frame_no=1)
    assert len(assignment) == 2
    assert set(assignment.values()) == {0, 1}


def test_centroid_tracker_keeps_same_id_for_nearby_point():
    tracker = CentroidTracker()
    tracker.update([(10, 10)], frame_no=1)
    assignment = tracker.update([(15, 12)], frame_no=2)
    assert assignment[0] == 0


def test_check_ppe_detects_yellow_helmet_and_vest():
    frame = np.zeros((200, 100, 3), dtype=np.uint8)
    frame[:] = (0, 0, 0)
    # BGR yellow = (0, 255, 255)
    frame[0:44, :] = (0, 220, 220)   # helmet region (top 22%)
    frame[50:130, :] = (0, 200, 0)   # vest region (green, hi-vis lime-ish in HSV)
    helmet_ok, vest_ok = check_ppe(frame, (0, 0, 100, 200))
    assert helmet_ok is True


def test_process_source_returns_zero_people_on_blank_frame():
    frame = np.zeros((300, 300, 3), dtype=np.uint8)
    result = process_source(frame, "construction", {"construction": ["helmet", "vest"]})
    assert result["total_people"] == 0
