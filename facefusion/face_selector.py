from typing import List

import numpy

from facefusion import state_manager
from facefusion.typing import Face, FaceSelectorAge, FaceSelectorGender, FaceSelectorOrder, FaceSet


def find_similar_faces(faces : List[Face], reference_faces : FaceSet, face_distance : float) -> List[Face]:
	similar_faces : List[Face] = []

	if faces and reference_faces:
		for reference_set in reference_faces:
			if not similar_faces:
				for reference_face in reference_faces[reference_set]:
					for face in faces:
						if compare_faces(face, reference_face, face_distance):
							similar_faces.append(face)
	return similar_faces


def compare_faces(face : Face, reference_face : Face, face_distance : float) -> bool:
	current_face_distance = calc_face_distance(face, reference_face)
	return current_face_distance < face_distance


def calc_face_distance(face : Face, reference_face : Face) -> float:
	if hasattr(face, 'normed_embedding') and hasattr(reference_face, 'normed_embedding'):
		return 1 - numpy.dot(face.normed_embedding, reference_face.normed_embedding)
	return 0


def sort_and_filter_faces(faces : List[Face]) -> List[Face]:
	if faces:
		if state_manager.get_item('face_selector_order'):
			faces = sort_by_order(faces, state_manager.get_item('face_selector_order'))
		if state_manager.get_item('face_selector_age'):
			faces = filter_by_age(faces, state_manager.get_item('face_selector_age'))
		if state_manager.get_item('face_selector_gender'):
			faces = filter_by_gender(faces, state_manager.get_item('face_selector_gender'))
	return faces


def sort_by_order(faces : List[Face], order : FaceSelectorOrder) -> List[Face]:
	if order == 'left-right':
		return sorted(faces, key = lambda face: face.bounding_box[0])
	if order == 'right-left':
		return sorted(faces, key = lambda face: face.bounding_box[0], reverse = True)
	if order == 'top-bottom':
		return sorted(faces, key = lambda face: face.bounding_box[1])
	if order == 'bottom-top':
		return sorted(faces, key = lambda face: face.bounding_box[1], reverse = True)
	if order == 'small-large':
		return sorted(faces, key = lambda face: (face.bounding_box[2] - face.bounding_box[0]) * (face.bounding_box[3] - face.bounding_box[1]))
	if order == 'large-small':
		return sorted(faces, key = lambda face: (face.bounding_box[2] - face.bounding_box[0]) * (face.bounding_box[3] - face.bounding_box[1]), reverse = True)
	if order == 'best-worst':
		return sorted(faces, key = lambda face: face.score_set.get('detector'), reverse = True)
	if order == 'worst-best':
		return sorted(faces, key = lambda face: face.score_set.get('detector'))
	return faces


def filter_by_age(faces : List[Face], age : FaceSelectorAge) -> List[Face]:
	filter_faces = []

	for face in faces:
		if categorize_age(face.age) == age:
			filter_faces.append(face)
	return filter_faces


def filter_by_gender(faces : List[Face], gender : FaceSelectorGender) -> List[Face]:
	filter_faces = []

	for face in faces:
		if categorize_gender(face.gender) == gender:
			filter_faces.append(face)
	return filter_faces


def categorize_age(age : int) -> FaceSelectorAge:
	if age < 13:
		return 'child'
	elif age < 19:
		return 'teen'
	elif age < 60:
		return 'adult'
	return 'senior'


def categorize_gender(gender : int) -> FaceSelectorGender:
	if gender == 0:
		return 'female'
	return 'male'
