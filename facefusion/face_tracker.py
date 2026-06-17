from bisect import bisect_left
from typing import List, Optional, Tuple

from facefusion.face_analyser import get_static_faces
from facefusion.face_creator import interpolate_face
from facefusion.face_helper import calculate_bounding_box_iou
from facefusion.types import Face, FaceTrack, VisionFrame


def track_faces(vision_frames : List[VisionFrame], target_index : int, iou_threshold : float) -> List[Face]:
	face_tracks = build_face_tracks(vision_frames, iou_threshold)
	track_faces = []

	for face_track in face_tracks:
		tracked_face = resolve_track_face(face_track, target_index)

		if tracked_face:
			track_faces.append(tracked_face)

	return track_faces


def build_face_tracks(vision_frames : List[VisionFrame], iou_threshold : float) -> List[FaceTrack]:
	face_tracks : List[FaceTrack] = []

	for frame_index, vision_frame in enumerate(vision_frames):
		for face in get_static_faces([ vision_frame ]):
			face_track = find_best_face_track(face_tracks, face, frame_index, iou_threshold)

			if face_track:
				face_track[frame_index] = face
			else:
				face_tracks.append({ frame_index : face })

	return face_tracks


def find_best_face_track(face_tracks : List[FaceTrack], face : Face, frame_index : int, iou_threshold : float) -> FaceTrack:
	best_track : FaceTrack = {}
	best_iou = iou_threshold

	for face_track in face_tracks:
		if frame_index not in face_track:
			anchor_index = get_nearest_track_index(face_track, frame_index)
			temp_iou = calculate_bounding_box_iou(face.bounding_box, face_track.get(anchor_index).bounding_box)

			if temp_iou > best_iou:
				best_iou = temp_iou
				best_track = face_track

	return best_track


def get_nearest_track_index(face_track : FaceTrack, target_index : int) -> int:
	anchor_index_previous, anchor_index_next = get_anchor_indices(face_track, target_index)

	if anchor_index_previous > -1 and anchor_index_next > -1:
		if anchor_index_next - target_index < target_index - anchor_index_previous:
			return anchor_index_next
		return anchor_index_previous

	if anchor_index_previous > -1:
		return anchor_index_previous

	return anchor_index_next


def get_anchor_indices(face_track : FaceTrack, target_index : int) -> Tuple[int, int]:
	track_indices = sorted(face_track.keys())
	position = bisect_left(track_indices, target_index)
	anchor_index_previous = -1
	anchor_index_next = -1

	if position > 0:
		anchor_index_previous = track_indices[position - 1]
	if position < len(track_indices):
		anchor_index_next = track_indices[position]

	return anchor_index_previous, anchor_index_next


def resolve_track_face(face_track : FaceTrack, target_index : int) -> Optional[Face]:
	if target_index in face_track:
		return face_track.get(target_index)

	anchor_index_previous, anchor_index_next = get_anchor_indices(face_track, target_index)

	if anchor_index_previous > -1 and anchor_index_next > -1:
		anchor_face_previous = face_track.get(anchor_index_previous)
		anchor_face_next = face_track.get(anchor_index_next)
		ratio = (target_index - anchor_index_previous) / (anchor_index_next - anchor_index_previous)
		return interpolate_face(anchor_face_previous, anchor_face_next, ratio)

	return None
