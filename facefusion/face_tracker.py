from typing import List, Tuple

from facefusion.common_helper import get_first, get_last
from facefusion.face_creator import get_static_faces, refill_faces
from facefusion.face_helper import calculate_bounding_box_overlap
from facefusion.types import Face, FaceTrack, VisionFrame


def track_faces(vision_frames : List[VisionFrame]) -> List[Face]:
	target_index = len(vision_frames) // 2
	face_tracks = build_face_tracks(vision_frames, 0.3)
	track_faces = []

	for face_track in face_tracks:
		track_indices = sorted(face_track)
		track_index_first = get_first(track_indices)
		track_index_last = get_last(track_indices)
		track_range = range(track_index_first, track_index_last + 1)

		if target_index in track_range:
			fill_faces = []

			for index in track_range:
				fill_faces.append(face_track.get(index))

			track_faces.append(refill_faces(fill_faces)[target_index - track_index_first])

	return track_faces


def build_face_tracks(vision_frames : List[VisionFrame], overlap_threshold : float) -> List[FaceTrack]:
	face_tracks : List[FaceTrack] = []

	for frame_index, vision_frame in enumerate(vision_frames):
		for face in get_static_faces([ vision_frame ]):
			face_track = find_best_face_track(face_tracks, face, frame_index, overlap_threshold)

			if face_track:
				face_track[frame_index] = face
			else:
				face_tracks.append({ frame_index : face })

	return face_tracks


def find_best_face_track(face_tracks : List[FaceTrack], face : Face, frame_index : int, overlap_threshold : float) -> FaceTrack:
	best_track : FaceTrack = {}
	best_overlap_threshold = overlap_threshold

	for face_track in face_tracks:
		if frame_index not in face_track:
			anchor_index = find_nearest_track_index(face_track, frame_index)
			temp_bounding_box_overlap = calculate_bounding_box_overlap(face.bounding_box, face_track.get(anchor_index).bounding_box)

			if temp_bounding_box_overlap > best_overlap_threshold:
				best_overlap_threshold = temp_bounding_box_overlap
				best_track = face_track

	return best_track


def find_nearest_track_index(face_track : FaceTrack, target_index : int) -> int:
	anchor_index_previous, anchor_index_next = get_anchor_indices(face_track, target_index)

	if anchor_index_previous > -1 and anchor_index_next > -1:
		if anchor_index_next - target_index < target_index - anchor_index_previous:
			return anchor_index_next
		return anchor_index_previous

	if anchor_index_previous > -1:
		return anchor_index_previous

	return anchor_index_next


def get_anchor_indices(face_track : FaceTrack, target_index : int) -> Tuple[int, int]:
	track_indices = sorted(face_track)
	anchor_index_previous = -1
	anchor_index_next = -1

	for track_index in track_indices:
		if track_index < target_index:
			anchor_index_previous = track_index

	for track_index in reversed(track_indices):
		if track_index > target_index:
			anchor_index_next = track_index

	return anchor_index_previous, anchor_index_next
