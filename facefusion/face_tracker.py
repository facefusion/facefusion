from bisect import bisect_left
from typing import Dict, List, Optional, Tuple

from facefusion.face_analyser import get_static_faces
from facefusion.face_helper import estimate_face_angle
from facefusion.types import BoundingBox, Face, FaceLandmarkSet, Points, VisionFrame


def track_faces(vision_frames : List[VisionFrame], target_index : int, iou_threshold : float) -> List[Face]:
	face_tracks = build_face_tracks(vision_frames, iou_threshold)
	tracked_faces = []

	for face_track in face_tracks:
		tracked_face = resolve_track_face(face_track, target_index)

		if tracked_face:
			tracked_faces.append(tracked_face)

	return tracked_faces


def build_face_tracks(vision_frames : List[VisionFrame], iou_threshold : float) -> List[Dict[int, Face]]:
	face_tracks : List[Dict[int, Face]] = []

	for frame_index, vision_frame in enumerate(vision_frames):
		for face in get_static_faces([ vision_frame ]):
			face_track = match_face_track(face_tracks, face, frame_index, iou_threshold)

			if face_track:
				face_track[frame_index] = face
			if not face_track:
				face_tracks.append({ frame_index : face })

	return face_tracks


def match_face_track(face_tracks : List[Dict[int, Face]], face : Face, frame_index : int, iou_threshold : float) -> Dict[int, Face]:
	best_track : Dict[int, Face] = {}
	best_iou = iou_threshold

	for face_track in face_tracks:
		if frame_index not in face_track:
			anchor_index = get_nearest_track_index(face_track, frame_index)
			current_iou = calculate_bounding_box_iou(face.bounding_box, face_track.get(anchor_index).bounding_box)

			if current_iou > best_iou:
				best_iou = current_iou
				best_track = face_track

	return best_track


def calculate_bounding_box_iou(bounding_box : BoundingBox, anchor_bounding_box : BoundingBox) -> float:
	box_x1, box_y1, box_x2, box_y2 = bounding_box
	anchor_x1, anchor_y1, anchor_x2, anchor_y2 = anchor_bounding_box
	intersection_x1 = max(box_x1, anchor_x1)
	intersection_y1 = max(box_y1, anchor_y1)
	intersection_x2 = min(box_x2, anchor_x2)
	intersection_y2 = min(box_y2, anchor_y2)
	intersection = max(0, intersection_x2 - intersection_x1) * max(0, intersection_y2 - intersection_y1)
	bounding_box_area = (box_x2 - box_x1) * (box_y2 - box_y1)
	anchor_bounding_box_area = (anchor_x2 - anchor_x1) * (anchor_y2 - anchor_y1)
	union = bounding_box_area + anchor_bounding_box_area - intersection

	if union > 0:
		return intersection / union

	return 0.0


def get_nearest_track_index(face_track : Dict[int, Face], target_index : int) -> int:
	anchor_index_before, anchor_index_after = get_anchor_indices(face_track, target_index)

	if anchor_index_before >= 0 and anchor_index_after >= 0:
		if target_index - anchor_index_before <= anchor_index_after - target_index:
			return anchor_index_before
		return anchor_index_after

	if anchor_index_before >= 0:
		return anchor_index_before

	return anchor_index_after


def get_anchor_indices(face_track : Dict[int, Face], target_index : int) -> Tuple[int, int]:
	track_indices = sorted(face_track.keys())
	position = bisect_left(track_indices, target_index)
	anchor_index_before = -1
	anchor_index_after = -1

	if position > 0:
		anchor_index_before = track_indices[position - 1]
	if position < len(track_indices):
		anchor_index_after = track_indices[position]

	return anchor_index_before, anchor_index_after


def resolve_track_face(face_track : Dict[int, Face], target_index : int) -> Optional[Face]:
	if target_index in face_track:
		return face_track.get(target_index)

	anchor_index_before, anchor_index_after = get_anchor_indices(face_track, target_index)

	if anchor_index_before >= 0 and anchor_index_after >= 0:
		anchor_face_before = face_track.get(anchor_index_before)
		anchor_face_after = face_track.get(anchor_index_after)
		ratio = (target_index - anchor_index_before) / (anchor_index_after - anchor_index_before)
		return interpolate_face(anchor_face_before, anchor_face_after, ratio)

	return None


def interpolate_face(anchor_face_before : Face, anchor_face_after : Face, ratio : float) -> Face:
	bounding_box = interpolate_array(anchor_face_before.bounding_box, anchor_face_after.bounding_box, ratio)
	landmark_set : FaceLandmarkSet =\
	{
		'5': interpolate_array(anchor_face_before.landmark_set.get('5'), anchor_face_after.landmark_set.get('5'), ratio),
		'5/68': interpolate_array(anchor_face_before.landmark_set.get('5/68'), anchor_face_after.landmark_set.get('5/68'), ratio),
		'68': interpolate_array(anchor_face_before.landmark_set.get('68'), anchor_face_after.landmark_set.get('68'), ratio),
		'68/5': interpolate_array(anchor_face_before.landmark_set.get('68/5'), anchor_face_after.landmark_set.get('68/5'), ratio)
	}
	anchor_face = anchor_face_before

	if ratio >= 0.5:
		anchor_face = anchor_face_after

	return anchor_face._replace(
		bounding_box = bounding_box,
		landmark_set = landmark_set,
		angle = estimate_face_angle(landmark_set.get('68/5'))
	)


def interpolate_array(array_before : Points, array_after : Points, ratio : float) -> Points:
	return array_before * (1 - ratio) + array_after * ratio
