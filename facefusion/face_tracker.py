from bisect import bisect_left
from typing import List, Optional, Tuple

from facefusion.face_analyser import get_static_faces
from facefusion.face_creator import interpolate_face
from facefusion.face_helper import calculate_bounding_box_iou
from facefusion.types import Face, FaceTrack, VisionFrame


def track_faces(vision_frames : List[VisionFrame], target_index : int, iou_threshold : float) -> List[Face]:
	face_tracks = build_face_tracks(vision_frames, iou_threshold)
	tracked_faces = []

	for face_track in face_tracks:
		tracked_face = resolve_track_face(face_track, target_index)

		if tracked_face:
			tracked_faces.append(tracked_face)

	return tracked_faces


def build_face_tracks(vision_frames : List[VisionFrame], iou_threshold : float) -> List[FaceTrack]:
	face_tracks : List[FaceTrack] = []

	for frame_index, vision_frame in enumerate(vision_frames):
		for face in get_static_faces([ vision_frame ]):
			face_track = match_face_track(face_tracks, face, frame_index, iou_threshold)

			if face_track:
				face_track[frame_index] = face
			if not face_track:
				face_tracks.append({ frame_index : face })

	return face_tracks


def match_face_track(face_tracks : List[FaceTrack], face : Face, frame_index : int, iou_threshold : float) -> FaceTrack:
	best_track : FaceTrack = {}
	best_iou = iou_threshold

	for face_track in face_tracks:
		if frame_index not in face_track:
			anchor_index = get_nearest_track_index(face_track, frame_index)
			current_iou = calculate_bounding_box_iou(face.bounding_box, face_track.get(anchor_index).bounding_box)

			if current_iou > best_iou:
				best_iou = current_iou
				best_track = face_track

	return best_track


def get_nearest_track_index(face_track : FaceTrack, target_index : int) -> int:
	anchor_index_before, anchor_index_after = get_anchor_indices(face_track, target_index)

	if anchor_index_before >= 0 and anchor_index_after >= 0:
		if target_index - anchor_index_before <= anchor_index_after - target_index:
			return anchor_index_before
		return anchor_index_after

	if anchor_index_before >= 0:
		return anchor_index_before

	return anchor_index_after


def get_anchor_indices(face_track : FaceTrack, target_index : int) -> Tuple[int, int]:
	track_indices = sorted(face_track.keys())
	position = bisect_left(track_indices, target_index)
	anchor_index_before = -1
	anchor_index_after = -1

	if position > 0:
		anchor_index_before = track_indices[position - 1]
	if position < len(track_indices):
		anchor_index_after = track_indices[position]

	return anchor_index_before, anchor_index_after


def resolve_track_face(face_track : FaceTrack, target_index : int) -> Optional[Face]:
	if target_index in face_track:
		return face_track.get(target_index)

	anchor_index_before, anchor_index_after = get_anchor_indices(face_track, target_index)

	if anchor_index_before >= 0 and anchor_index_after >= 0:
		anchor_face_before = face_track.get(anchor_index_before)
		anchor_face_after = face_track.get(anchor_index_after)
		ratio = (target_index - anchor_index_before) / (anchor_index_after - anchor_index_before)
		return interpolate_face(anchor_face_before, anchor_face_after, ratio)

	return None
