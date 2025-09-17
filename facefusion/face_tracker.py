"""Lightweight landmark tracker to reduce expensive per-frame face detection."""
from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Callable, Dict, List, Optional

import cv2
import numpy

from facefusion import state_manager
from facefusion.face_helper import convert_to_face_landmark_5, estimate_face_angle
from facefusion.types import Face, VisionFrame


@dataclass
class _TrackedFace:
    track_id: int
    face: Face
    points_68: numpy.ndarray
    misses: int = 0
    last_detection_frame: int = 0


class FaceTracker:
    def __init__(self) -> None:
        self._tracks: Dict[int, _TrackedFace] = {}
        self._next_track_id = 0
        self._prev_gray: Optional[numpy.ndarray] = None
        self._frame_index: int = 0
        self._lock = Lock()
        # Config defaults
        self._detection_interval = 6
        self._max_missed = 2
        self._min_points = 10
        self._match_iou = 0.3
        self._config_signature: Optional[tuple[int, int, int, float]] = None

    def reset(self) -> None:
        with self._lock:
            self._tracks.clear()
            self._next_track_id = 0
            self._prev_gray = None
            self._frame_index = 0

    def process_frame(self, vision_frame: VisionFrame, detect_fn: Callable[[VisionFrame], List[Face]]) -> List[Face]:
        with self._lock:
            return self._process_frame_locked(vision_frame, detect_fn)

    # Internal helpers -----------------------------------------------------
    def _process_frame_locked(self, vision_frame: VisionFrame, detect_fn: Callable[[VisionFrame], List[Face]]) -> List[Face]:
        self._refresh_config()
        gray = cv2.cvtColor(vision_frame, cv2.COLOR_BGR2GRAY)
        self._frame_index += 1

        need_detection = (self._prev_gray is None or not self._tracks or
                          (self._detection_interval > 0 and (self._frame_index % self._detection_interval == 0)))

        faces: List[Face]
        if need_detection:
            faces = detect_fn(vision_frame)
            faces = self._assign_detections(faces)
        else:
            faces = self._track_existing(gray)
            # If tracking failed for all faces, fall back to detection immediately
            if not faces:
                faces = detect_fn(vision_frame)
                faces = self._assign_detections(faces)

        self._prev_gray = gray
        if faces:
            faces = sorted(faces, key=lambda f: f.bounding_box[0])
        return faces

    def _refresh_config(self) -> None:
        interval = state_manager.get_item('face_tracker_detection_interval')
        max_missed = state_manager.get_item('face_tracker_max_missed')
        min_points = state_manager.get_item('face_tracker_min_points')
        match_iou = state_manager.get_item('face_tracker_match_iou')

        interval_val = int(interval) if isinstance(interval, int) else 6
        max_missed_val = int(max_missed) if isinstance(max_missed, int) else 2
        min_points_val = int(min_points) if isinstance(min_points, int) else 10
        match_iou_val = float(match_iou) if isinstance(match_iou, (int, float)) else 0.3

        interval_val = max(1, interval_val)
        max_missed_val = max(0, max_missed_val)
        min_points_val = max(5, min_points_val)
        match_iou_val = min(0.9, max(0.1, match_iou_val))

        signature = (interval_val, max_missed_val, min_points_val, match_iou_val)
        if signature != self._config_signature:
            self._detection_interval = interval_val
            self._max_missed = max_missed_val
            self._min_points = min_points_val
            self._match_iou = match_iou_val
            self._config_signature = signature

    def _assign_detections(self, faces: List[Face]) -> List[Face]:
        assigned: List[Face] = []
        unmatched_track_ids = set(self._tracks.keys())

        for face in faces:
            matched_id = self._match_track(face, unmatched_track_ids)
            if matched_id is not None:
                track = self._tracks[matched_id]
                track.face = face
                track.points_68 = face.landmark_set.get('68').astype(numpy.float32)
                track.misses = 0
                track.last_detection_frame = self._frame_index
                unmatched_track_ids.discard(matched_id)
                assigned.append(track.face)
            else:
                assigned.append(self._create_track(face))

        for track_id in list(unmatched_track_ids):
            track = self._tracks.get(track_id)
            if track is None:
                continue
            track.misses += 1
            if track.misses > self._max_missed:
                del self._tracks[track_id]

        return assigned

    def _match_track(self, face: Face, candidates: set[int]) -> Optional[int]:
        if not candidates:
            return None
        face_box = face.bounding_box.astype(numpy.float32)
        best_id: Optional[int] = None
        best_iou = 0.0
        for track_id in list(candidates):
            track = self._tracks[track_id]
            iou = _compute_iou(face_box, track.face.bounding_box.astype(numpy.float32))
            if iou >= self._match_iou and iou > best_iou:
                best_iou = iou
                best_id = track_id
        return best_id

    def _create_track(self, face: Face) -> Face:
        landmarks = face.landmark_set.get('68')
        if landmarks is None:
            return face
        track = _TrackedFace(
            track_id=self._next_track_id,
            face=face,
            points_68=landmarks.astype(numpy.float32).copy(),
            last_detection_frame=self._frame_index,
        )
        self._tracks[self._next_track_id] = track
        self._next_track_id += 1
        return track.face

    def _track_existing(self, gray: numpy.ndarray) -> List[Face]:
        if self._prev_gray is None or not self._tracks:
            return []

        tracked_faces: List[Face] = []
        remove_ids: List[int] = []
        h, w = gray.shape

        for track_id, track in list(self._tracks.items()):
            prev_points = track.points_68.reshape(-1, 1, 2).astype(numpy.float32)
            try:
                next_points, status, _ = cv2.calcOpticalFlowPyrLK(
                    self._prev_gray, gray, prev_points, None,
                    winSize=(21, 21), maxLevel=3,
                    criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)
                )
            except cv2.error:
                track.misses += 1
                if track.misses > self._max_missed:
                    remove_ids.append(track_id)
                continue

            if next_points is None or status is None:
                track.misses += 1
                if track.misses > self._max_missed:
                    remove_ids.append(track_id)
                continue

            status_mask = status.reshape(-1).astype(bool)
            valid_count = int(status_mask.sum())

            if valid_count < self._min_points:
                track.misses += 1
                if track.misses > self._max_missed:
                    remove_ids.append(track_id)
                continue

            updated = track.points_68.copy()
            updated[status_mask] = next_points.reshape(-1, 2)[status_mask]
            track.points_68 = updated

            min_xy = updated.min(axis=0)
            max_xy = updated.max(axis=0)

            min_x = float(numpy.clip(min_xy[0], 0, w - 1))
            min_y = float(numpy.clip(min_xy[1], 0, h - 1))
            max_x = float(numpy.clip(max_xy[0], 0, w - 1))
            max_y = float(numpy.clip(max_xy[1], 0, h - 1))

            if max_x - min_x < 1 or max_y - min_y < 1:
                track.misses += 1
                if track.misses > self._max_missed:
                    remove_ids.append(track_id)
                continue

            landmark_68 = updated.astype(numpy.float32)
            landmark_5 = convert_to_face_landmark_5(landmark_68)
            landmark_set = {
                '5': landmark_5,
                '5/68': landmark_5,
                '68': landmark_68,
                '68/5': landmark_68
            }
            bounding_box = numpy.array([min_x, min_y, max_x, max_y], dtype=numpy.float32)
            angle = estimate_face_angle(landmark_68)
            track.face = track.face._replace(
                bounding_box=bounding_box,
                landmark_set=landmark_set,
                angle=angle
            )
            track.misses = 0
            tracked_faces.append(track.face)

        for track_id in remove_ids:
            self._tracks.pop(track_id, None)

        return tracked_faces


def _compute_iou(box_a: numpy.ndarray, box_b: numpy.ndarray) -> float:
    x1 = max(float(box_a[0]), float(box_b[0]))
    y1 = max(float(box_a[1]), float(box_b[1]))
    x2 = min(float(box_a[2]), float(box_b[2]))
    y2 = min(float(box_a[3]), float(box_b[3]))
    inter_w = max(0.0, x2 - x1)
    inter_h = max(0.0, y2 - y1)
    inter_area = inter_w * inter_h
    if inter_area <= 0:
        return 0.0
    area_a = max(0.0, float(box_a[2] - box_a[0])) * max(0.0, float(box_a[3] - box_a[1]))
    area_b = max(0.0, float(box_b[2] - box_b[0])) * max(0.0, float(box_b[3] - box_b[1]))
    denom = area_a + area_b - inter_area
    if denom <= 0:
        return 0.0
    return inter_area / denom


_GLOBAL_TRACKER: Optional[FaceTracker] = None


def get_tracker() -> FaceTracker:
    global _GLOBAL_TRACKER
    if _GLOBAL_TRACKER is None:
        _GLOBAL_TRACKER = FaceTracker()
    return _GLOBAL_TRACKER


def reset_tracker() -> None:
    tracker = get_tracker()
    tracker.reset()


def is_enabled() -> bool:
    enabled = state_manager.get_item('enable_face_tracking')
    if enabled is None:
        return True
    return bool(enabled)
