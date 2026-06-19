from typing import List

from facefusion.common_helper import get_first, get_last
from facefusion.face_creator import get_static_faces, refill_faces
from facefusion.face_helper import calculate_bounding_box_overlap
from facefusion.types import Face, FaceTrack, VisionFrame


def track_faces(vision_frames : List[VisionFrame]) -> List[Face]:
	target_index = len(vision_frames) // 2
	face_tracks = create_face_tracks(vision_frames, 0.3)
	temp_faces = []

	for face_track in face_tracks:
		track_indices = sorted(face_track)
		track_index_first = get_first(track_indices)
		track_index_last = get_last(track_indices)
		track_range = range(track_index_first, track_index_last + 1)

		if target_index in track_range:
			fill_faces = []

			for index in track_range:
				fill_faces.append(face_track.get(index))

			temp_faces.append(refill_faces(fill_faces)[target_index - track_index_first])

	return temp_faces


def create_face_tracks(vision_frames : List[VisionFrame], overlap_threshold : float) -> List[FaceTrack]:
	face_tracks : List[FaceTrack] = []

	for frame_index, vision_frame in enumerate(vision_frames):
		for face in get_static_faces([ vision_frame ]):
			face_track = select_face_track(face_tracks, face, overlap_threshold)

			if face_track:
				face_track[frame_index] = face
			else:
				face_tracks.append({ frame_index : face })

	return face_tracks


def select_face_track(face_tracks : List[FaceTrack], face : Face, overlap_threshold : float) -> FaceTrack:
	best_track : FaceTrack = {}
	best_overlap_threshold = overlap_threshold

	for face_track in face_tracks:
		track_face = face_track.get(get_last(sorted(face_track)))
		track_overlap = calculate_bounding_box_overlap(face.bounding_box, track_face.bounding_box)

		if track_overlap > best_overlap_threshold:
			best_overlap_threshold = track_overlap
			best_track = face_track

	return best_track
