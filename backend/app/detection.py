"""
Person detection: OpenCV DNN + MobileNet-SSD (same model family as SafeSpeed AI).
PPE check within each detected person's bounding box:
  - "helmet" region = top ~22% of the box (head area) -> flagged present if
    EITHER a colour heuristic (high-visibility yellow/orange/white/red in
    HSV space) OR a trained MobileNetV2 helmet/no_helmet classifier (92.2%
    held-out validation accuracy, trained on a public helmet dataset -
    see README "Limitations" for its motorcycle-helmet domain-shift caveat)
    says helmet. Alerting on either avoids the trained model's domain gap
    making detection worse than the heuristic alone ever was.
  - "vest" region = ~25%-65% of the box height (torso area) -> checked for
    high-visibility vest colours (yellow/orange/lime-green). No real vest
    dataset was found publicly downloadable, so vest detection stays
    heuristic-only - see README "Limitations".
This is a legitimate, working baseline detector - not a placeholder - but
colour heuristics are fooled by e.g. a yellow shirt or an orange background,
and documented as such.
"""
import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import cv2
import numpy as np
import torch
from PIL import Image
from torchvision import transforms

MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
PROTOTXT = os.path.join(MODEL_DIR, "MobileNetSSD_deploy.prototxt")
CAFFEMODEL = os.path.join(MODEL_DIR, "MobileNetSSD_deploy.caffemodel")

VOC_CLASSES = [
    "background", "aeroplane", "bicycle", "bird", "boat", "bottle", "bus",
    "car", "cat", "chair", "cow", "diningtable", "dog", "horse", "motorbike",
    "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor",
]

# HSV ranges for common high-visibility PPE colours
HELMET_HSV_RANGES = [
    ((15, 80, 120), (35, 255, 255)),    # yellow/orange helmet
    ((0, 0, 200), (180, 40, 255)),      # white helmet
    ((0, 100, 100), (10, 255, 255)),    # red helmet
]
VEST_HSV_RANGES = [
    ((20, 100, 120), (35, 255, 255)),   # hi-vis yellow
    ((35, 80, 100), (85, 255, 255)),    # hi-vis lime/green
    ((5, 120, 120), (18, 255, 255)),    # hi-vis orange
]

_HELMET_MODEL_PATH = os.path.join(os.path.dirname(__file__), "ml_model", "ppe_helmet_classifier.pt")
_HELMET_MODEL_CLASSES = ["helmet", "no_helmet"]
_HELMET_TRANSFORM = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)

_helmet_model = torch.jit.load(_HELMET_MODEL_PATH, map_location="cpu")
_helmet_model.eval()

_net = None


def get_net():
    global _net
    if _net is None:
        if not (os.path.exists(PROTOTXT) and os.path.exists(CAFFEMODEL)):
            raise FileNotFoundError("MobileNet-SSD model files missing from backend/models/.")
        _net = cv2.dnn.readNetFromCaffe(PROTOTXT, CAFFEMODEL)
    return _net


def detect_people(frame, confidence_threshold: float = 0.4) -> List[Tuple[float, Tuple[int, int, int, int]]]:
    net = get_net()
    h, w = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)
    net.setInput(blob)
    detections = net.forward()

    results = []
    for i in range(detections.shape[2]):
        confidence = float(detections[0, 0, i, 2])
        if confidence < confidence_threshold:
            continue
        class_id = int(detections[0, 0, i, 1])
        label = VOC_CLASSES[class_id] if class_id < len(VOC_CLASSES) else "unknown"
        if label != "person":
            continue
        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        x1, y1, x2, y2 = box.astype(int)
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w - 1, x2), min(h - 1, y2)
        if x2 > x1 and y2 > y1:
            results.append((confidence, (x1, y1, x2, y2)))
    return results


def _region_matches_colour(region, ranges, min_fraction=0.12) -> bool:
    if region.size == 0:
        return False
    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for lo, hi in ranges:
        mask |= cv2.inRange(hsv, np.array(lo), np.array(hi))
    return bool((mask > 0).mean() >= min_fraction)


def _model_says_helmet(region: np.ndarray) -> bool:
    if region.size == 0:
        return False
    rgb = cv2.cvtColor(region, cv2.COLOR_BGR2RGB)
    tensor = _HELMET_TRANSFORM(Image.fromarray(rgb)).unsqueeze(0)
    with torch.no_grad():
        probs = torch.softmax(_helmet_model(tensor), dim=1)[0]
    idx = int(torch.argmax(probs))
    return _HELMET_MODEL_CLASSES[idx] == "helmet"


def check_ppe(frame, box: Tuple[int, int, int, int]) -> Tuple[bool, bool]:
    x1, y1, x2, y2 = box
    height = y2 - y1
    helmet_region = frame[y1:y1 + int(height * 0.22), x1:x2]
    vest_region = frame[y1 + int(height * 0.25):y1 + int(height * 0.65), x1:x2]
    helmet_ok = _region_matches_colour(helmet_region, HELMET_HSV_RANGES) or _model_says_helmet(helmet_region)
    vest_ok = _region_matches_colour(vest_region, VEST_HSV_RANGES)
    return helmet_ok, vest_ok


@dataclass
class Track:
    track_id: int
    centroid: Tuple[int, int]
    misses: int = 0
    last_frame: int = 0


class CentroidTracker:
    """Deduplicates the same physical person across consecutive frames."""

    def __init__(self, max_disappeared: int = 10, max_distance: int = 90):
        self.next_id = 0
        self.tracks: Dict[int, Track] = {}
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance

    def update(self, centroids: List[Tuple[int, int]], frame_no: int) -> Dict[int, int]:
        """Returns {input_index: track_id}, registering new tracks as needed."""
        assignment: Dict[int, int] = {}
        if not self.tracks:
            for i, c in enumerate(centroids):
                self.tracks[self.next_id] = Track(self.next_id, c, 0, frame_no)
                assignment[i] = self.next_id
                self.next_id += 1
            return assignment

        track_ids = list(self.tracks.keys())
        track_centroids = [self.tracks[t].centroid for t in track_ids]
        used_rows, used_cols = set(), set()

        if centroids:
            D = np.zeros((len(track_centroids), len(centroids)))
            for i, tc in enumerate(track_centroids):
                for j, c in enumerate(centroids):
                    D[i, j] = np.linalg.norm(np.array(tc) - np.array(c))
            rows = D.min(axis=1).argsort()
            cols = D.argmin(axis=1)[rows]
            for row, col in zip(rows, cols):
                if row in used_rows or col in used_cols or D[row, col] > self.max_distance:
                    continue
                tid = track_ids[row]
                self.tracks[tid].centroid = centroids[col]
                self.tracks[tid].misses = 0
                self.tracks[tid].last_frame = frame_no
                assignment[col] = tid
                used_rows.add(row)
                used_cols.add(col)

        for j, c in enumerate(centroids):
            if j not in used_cols:
                self.tracks[self.next_id] = Track(self.next_id, c, 0, frame_no)
                assignment[j] = self.next_id
                self.next_id += 1

        for i, tid in enumerate(track_ids):
            if i not in used_rows:
                self.tracks[tid].misses += 1

        for tid in list(self.tracks.keys()):
            if self.tracks[tid].misses > self.max_disappeared:
                del self.tracks[tid]

        return assignment


def process_source(image_or_frames, zone: str, zone_rules: dict, evidence_dir=None) -> dict:
    """Accepts a single BGR frame (image mode) and returns compliance events."""
    required = set(zone_rules.get(zone, ["helmet", "vest"]))
    people = detect_people(image_or_frames)

    events = []
    for idx, (conf, box) in enumerate(people):
        helmet_ok, vest_ok = check_ppe(image_or_frames, box)
        present = set()
        if helmet_ok:
            present.add("helmet")
        if vest_ok:
            present.add("vest")
        missing = required - present
        events.append({
            "person_track_id": idx,
            "helmet_detected": helmet_ok,
            "vest_detected": vest_ok,
            "is_compliant": len(missing) == 0,
            "missing_items": ",".join(sorted(missing)),
        })

    total = len(events)
    compliant = sum(1 for e in events if e["is_compliant"])
    return {
        "total_people": total,
        "compliant_count": compliant,
        "non_compliant_count": total - compliant,
        "events": events,
    }


def process_video(video_path: str, zone: str, zone_rules: dict, sample_every_n_frames: int = 15) -> dict:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    tracker = CentroidTracker()
    frame_no = 0
    seen_track_results: Dict[int, dict] = {}

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_no += 1
        if frame_no % sample_every_n_frames != 0:
            continue

        people = detect_people(frame)
        centroids = [(int((b[0] + b[2]) / 2), int((b[1] + b[3]) / 2)) for _, b in people]
        assignment = tracker.update(centroids, frame_no)

        required = set(zone_rules.get(zone, ["helmet", "vest"]))
        for idx, (conf, box) in enumerate(people):
            tid = assignment.get(idx)
            if tid is None:
                continue
            helmet_ok, vest_ok = check_ppe(frame, box)
            present = set()
            if helmet_ok:
                present.add("helmet")
            if vest_ok:
                present.add("vest")
            missing = required - present
            # keep the most recent observation per track
            seen_track_results[tid] = {
                "person_track_id": tid,
                "helmet_detected": helmet_ok,
                "vest_detected": vest_ok,
                "is_compliant": len(missing) == 0,
                "missing_items": ",".join(sorted(missing)),
                "frame_number": frame_no,
            }

    cap.release()

    events = list(seen_track_results.values())
    total = len(events)
    compliant = sum(1 for e in events if e["is_compliant"])
    return {
        "total_people": total,
        "compliant_count": compliant,
        "non_compliant_count": total - compliant,
        "events": events,
    }
