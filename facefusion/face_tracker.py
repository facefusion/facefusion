from typing import List

from facefusion.common_helper import get_first, get_last
from facefusion.face_creator import get_static_faces, refill_faces
from facefusion.face_helper import calculate_bounding_box_overlap
from facefusion.types import Face, FaceTrack, Score, VisionFrame


def track_faces(vision_frames : List[VisionFrame], score : Score) -> List[Face]:
	target_index = len(vision_frames) // 2
	face_tracks = create_face_tracks(vision_frames, score)
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


def create_face_tracks(vision_frames : List[VisionFrame], score : Score) -> List[FaceTrack]:
	face_tracks : List[FaceTrack] = []

	for frame_index, vision_frame in enumerate(vision_frames):
		for face in get_static_faces([ vision_frame ]):
			face_track = select_face_track(face_tracks, face, score)

			if face_track:
				face_track[frame_index] = face
			else:
				face_tracks.append(
				{
					frame_index : face
				})

	return face_tracks


def select_face_track(face_tracks : List[FaceTrack], face : Face, score : Score) -> FaceTrack:
	select_track : FaceTrack = {}
	select_score = score

	for face_track in face_tracks:
		track_face = face_track.get(get_last(face_track))
		track_score = calculate_bounding_box_overlap(face.bounding_box, track_face.bounding_box)

		if track_score > select_score:
			select_score = track_score
			select_track = face_track

	return select_track
