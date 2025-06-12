from typing import List

import numpy

from facefusion import state_manager
from facefusion.types import Face, FaceSelectorOrder, FaceSet, Gender, Race, Score


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
	current_face_distance = float(numpy.interp(current_face_distance, [ 0, 2 ], [ 0, 1 ]))
	return current_face_distance < face_distance


def calc_face_distance(face : Face, reference_face : Face) -> float:
	if hasattr(face, 'normed_embedding') and hasattr(reference_face, 'normed_embedding'):
		return 1 - numpy.dot(face.normed_embedding, reference_face.normed_embedding)
	return 0


def sort_and_filter_faces(faces : List[Face]) -> List[Face]:
	if faces:
		if state_manager.get_item('face_selector_order'):
			faces = sort_faces_by_order(faces, state_manager.get_item('face_selector_order'))
		if state_manager.get_item('face_selector_gender'):
			faces = filter_faces_by_gender(faces, state_manager.get_item('face_selector_gender'))
		if state_manager.get_item('face_selector_race'):
			faces = filter_faces_by_race(faces, state_manager.get_item('face_selector_race'))
		if state_manager.get_item('face_selector_age_start') or state_manager.get_item('face_selector_age_end'):
			faces = filter_faces_by_age(faces, state_manager.get_item('face_selector_age_start'), state_manager.get_item('face_selector_age_end'))
	return faces


def sort_faces_by_order(faces : List[Face], order : FaceSelectorOrder) -> List[Face]:
	if order == 'left-right':
		return sorted(faces, key = get_bounding_box_left)
	if order == 'right-left':
		return sorted(faces, key = get_bounding_box_left, reverse = True)
	if order == 'top-bottom':
		return sorted(faces, key = get_bounding_box_top)
	if order == 'bottom-top':
		return sorted(faces, key = get_bounding_box_top, reverse = True)
	if order == 'small-large':
		return sorted(faces, key = get_bounding_box_area)
	if order == 'large-small':
		return sorted(faces, key = get_bounding_box_area, reverse = True)
	if order == 'best-worst':
		return sorted(faces, key = get_face_detector_score, reverse = True)
	if order == 'worst-best':
		return sorted(faces, key = get_face_detector_score)
	return faces


def get_bounding_box_left(face : Face) -> float:
	return face.bounding_box[0]


def get_bounding_box_top(face : Face) -> float:
	return face.bounding_box[1]


def get_bounding_box_area(face : Face) -> float:
	return (face.bounding_box[2] - face.bounding_box[0]) * (face.bounding_box[3] - face.bounding_box[1])


def get_face_detector_score(face : Face) -> Score:
	return face.score_set.get('detector')


def filter_faces_by_gender(faces : List[Face], gender : Gender) -> List[Face]:
	filter_faces = []

	for face in faces:
		if face.gender == gender:
			filter_faces.append(face)
	return filter_faces


def filter_faces_by_age(faces : List[Face], face_selector_age_start : int, face_selector_age_end : int) -> List[Face]:
	filter_faces = []
	age = range(face_selector_age_start, face_selector_age_end)

	for face in faces:
		if set(face.age) & set(age):
			filter_faces.append(face)
	return filter_faces


def filter_faces_by_race(faces : List[Face], race : Race) -> List[Face]:
	filter_faces = []

	for face in faces:
		if face.race == race:
			filter_faces.append(face)
	return filter_faces
