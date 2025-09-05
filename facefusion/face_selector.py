from typing import List

import numpy

from facefusion import state_manager
from facefusion.face_analyser import get_many_faces, get_one_face
from facefusion.types import Face, FaceSelectorOrder, Gender, Race, Score, VisionFrame


def select_faces(reference_vision_frame : VisionFrame, target_vision_frame : VisionFrame) -> List[Face]:
	target_faces = get_many_faces([ target_vision_frame ])

	if state_manager.get_item('face_selector_mode') == 'many':
		return sort_and_filter_faces(target_faces)

	if state_manager.get_item('face_selector_mode') == 'one':
		target_face = get_one_face(sort_and_filter_faces(target_faces))
		if target_face:
			return [ target_face ]

	if state_manager.get_item('face_selector_mode') == 'reference':
		reference_faces = get_many_faces([ reference_vision_frame ])
		reference_faces = sort_and_filter_faces(reference_faces)
		reference_face = get_one_face(reference_faces, state_manager.get_item('reference_face_position'))
		if reference_face:
			match_faces = find_match_faces([ reference_face ], target_faces, state_manager.get_item('reference_face_distance'))
			return match_faces

	return []


def find_match_faces(reference_faces : List[Face], target_faces : List[Face], face_distance : float) -> List[Face]:
	match_faces : List[Face] = []

	for reference_face in reference_faces:
		if reference_face:
			for index, target_face in enumerate(target_faces):
				if compare_faces(target_face, reference_face, face_distance):
					match_faces.append(target_faces[index])

	return match_faces


def compare_faces(face : Face, reference_face : Face, face_distance : float) -> bool:
	current_face_distance = calculate_face_distance(face, reference_face)
	current_face_distance = float(numpy.interp(current_face_distance, [ 0, 2 ], [ 0, 1 ]))
	return current_face_distance < face_distance


def calculate_face_distance(face : Face, reference_face : Face) -> float:
	if hasattr(face, 'embedding_norm') and hasattr(reference_face, 'embedding_norm'):
		return 1 - numpy.dot(face.embedding_norm, reference_face.embedding_norm)
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
