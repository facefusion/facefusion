from typing import List, Optional

from facefusion.common_helper import get_first, get_middle
from facefusion.face_helper import estimate_face_angle
from facefusion.types import Face, FaceLandmarkSet, Points


def interpolate_faces(faces : List[Optional[Face]]) -> List[Face]:
	interpolate_faces = []
	anchor_index_previous = -1

	for index, face in enumerate(faces):
		if face:
			for gap_index in range(anchor_index_previous + 1, index):
				ratio = (gap_index - anchor_index_previous) / (index - anchor_index_previous)
				interpolate_faces.append(linear_blend_face([ faces[anchor_index_previous], face ], ratio))

			interpolate_faces.append(face)
			anchor_index_previous = index

	return interpolate_faces


def linear_blend_face(faces : List[Face], ratio : float) -> Face:
	face_previous = get_first(faces)
	face_next = get_middle(faces)
	anchor_face = face_next

	if ratio < 0.5:
		anchor_face = face_previous

	landmark_set : FaceLandmarkSet =\
	{
		'5': linear_blend_points(face_previous.landmark_set.get('5'), face_next.landmark_set.get('5'), ratio),
		'5/68': linear_blend_points(face_previous.landmark_set.get('5/68'), face_next.landmark_set.get('5/68'), ratio),
		'68': linear_blend_points(face_previous.landmark_set.get('68'), face_next.landmark_set.get('68'), ratio),
		'68/5': linear_blend_points(face_previous.landmark_set.get('68/5'), face_next.landmark_set.get('68/5'), ratio)
	}
	return Face(
		bounding_box = linear_blend_points(face_previous.bounding_box, face_next.bounding_box, ratio),
		score_set = anchor_face.score_set,
		landmark_set = landmark_set,
		angle = estimate_face_angle(landmark_set.get('68/5')),
		embedding = anchor_face.embedding,
		embedding_norm = anchor_face.embedding_norm,
		gender = anchor_face.gender,
		age = anchor_face.age,
		race = anchor_face.race
	)


def linear_blend_points(points_before : Points, points_after : Points, ratio : float) -> Points:
	return points_before * (1 - ratio) + points_after * ratio
