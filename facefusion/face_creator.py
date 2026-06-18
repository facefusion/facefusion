from typing import List, Optional

from facefusion.face_helper import estimate_face_angle
from facefusion.types import Face, FaceLandmarkSet, Points


def refill_faces(faces : List[Optional[Face]]) -> List[Face]:
	fill_faces = []
	anchor_index_previous = -1

	for index, face in enumerate(faces):
		if face:
			for gap_index in range(anchor_index_previous + 1, index):
				average_factor = (gap_index - anchor_index_previous) / (index - anchor_index_previous)
				fill_faces.append(average_face(faces[anchor_index_previous], face, average_factor))

			fill_faces.append(face)
			anchor_index_previous = index

	return fill_faces


def average_face(face_previous : Face, face_next : Face, average_factor : float) -> Face:
	face_anchor = face_next

	if average_factor < 0.5:
		face_anchor = face_previous

	landmark_set : FaceLandmarkSet =\
	{
		'5': average_points(face_previous.landmark_set.get('5'), face_next.landmark_set.get('5'), average_factor),
		'5/68': average_points(face_previous.landmark_set.get('5/68'), face_next.landmark_set.get('5/68'), average_factor),
		'68': average_points(face_previous.landmark_set.get('68'), face_next.landmark_set.get('68'), average_factor),
		'68/5': average_points(face_previous.landmark_set.get('68/5'), face_next.landmark_set.get('68/5'), average_factor)
	}

	return Face(
		bounding_box = average_points(face_previous.bounding_box, face_next.bounding_box, average_factor),
		score_set = face_anchor.score_set,
		landmark_set = landmark_set,
		angle = estimate_face_angle(landmark_set.get('68/5')),
		embedding = face_anchor.embedding,
		embedding_norm = face_anchor.embedding_norm,
		gender = face_anchor.gender,
		age = face_anchor.age,
		race = face_anchor.race
	)


def average_points(points_previous : Points, points_next : Points, average_factor : float) -> Points:
	return points_previous * (1 - average_factor) + points_next * average_factor
