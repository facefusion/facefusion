from typing import List, Optional, Tuple

from facefusion.face_analyser import get_static_faces
from facefusion.face_helper import calculate_face_distance, calculate_iou
from facefusion.types import BoundingBox, Face, VisionFrame


def propagate_reference_face(reference_face : Face, reference_faces : List[Face], target_vision_frames : List[VisionFrame]) -> List[Face]:
	reference_negatives = [ face for face in reference_faces if face is not reference_face ]
	window_faces = [ get_static_faces([ target_vision_frame ]) for target_vision_frame in target_vision_frames ]
	center_index = len(window_faces) // 2
	center_face = None
	center_distance = 2.0

	for target_face in window_faces[center_index]:
		for track_index, tracked_face in track_face(target_face, window_faces, center_index):
			negative_faces = reference_negatives + [ face for face in window_faces[track_index] if face is not tracked_face ]
			current_distance = calculate_face_distance(tracked_face, reference_face)
			if current_distance < center_distance and is_reference_identity(tracked_face, reference_face, negative_faces):
				center_face = target_face
				center_distance = current_distance

	if center_face:
		return [ center_face ]

	return []


def track_face(target_face : Face, window_faces : List[List[Face]], center_index : int) -> List[Tuple[int, Face]]:
	track = [ (center_index, target_face) ]

	for step in (1, -1):
		face = target_face
		index = center_index + step

		while face and 0 <= index < len(window_faces):
			face = find_face_by_iou(window_faces[index], face.bounding_box)
			if face:
				track.append((index, face))
			index += step

	return track


def is_reference_identity(target_face : Face, reference_face : Face, negative_faces : List[Face]) -> bool:
	identity_margin = 0.1
	bridge_distance = 1.0
	reference_distance = calculate_face_distance(target_face, reference_face)

	if reference_distance < bridge_distance:
		if negative_faces:
			negative_distance = min(calculate_face_distance(target_face, negative_face) for negative_face in negative_faces)
			return reference_distance + identity_margin < negative_distance
		return True

	return False


def find_face_by_iou(target_faces : List[Face], bounding_box : BoundingBox) -> Optional[Face]:
	match_face = None
	match_iou = 0.3

	for target_face in target_faces:
		current_iou = calculate_iou(target_face.bounding_box, bounding_box)
		if current_iou > match_iou:
			match_iou = current_iou
			match_face = target_face

	return match_face
