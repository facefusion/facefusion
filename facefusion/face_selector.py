from typing import List, Optional, Tuple

import numpy

import facefusion.choices
from facefusion import state_manager
from facefusion.common_helper import get_first, get_middle
from facefusion.face_creator import average_face_identity, get_one_face, get_static_faces
from facefusion.face_tracker import track_faces
from facefusion.types import Face, FaceSelectorOrder, Gender, Race, ReferenceFaceSet, Score, VisionFrame


def select_faces(reference_vision_frames : List[VisionFrame], source_vision_frames : List[VisionFrame], target_vision_frames : List[VisionFrame]) -> Tuple[List[Face], List[Face]]:
	source_faces = get_static_faces(source_vision_frames)

	if state_manager.get_item('face_tracker_score') > 0:
		target_faces = track_faces(target_vision_frames, state_manager.get_item('face_tracker_score'))
	else:
		target_faces = get_static_faces([ get_middle(target_vision_frames) ])

	if state_manager.get_item('face_selector_mode') == 'many':
		source_face = extract_one_face(source_vision_frames)
		__source_faces__ : List[Face] = []
		match_faces : List[Face] = []

		for target_face in sort_and_filter_faces(source_faces, target_faces):
			__source_faces__.append(source_face)
			match_faces.append(target_face)

		return __source_faces__, match_faces

	if state_manager.get_item('face_selector_mode') == 'one':
		source_face = extract_one_face(source_vision_frames)
		target_face = get_one_face(sort_and_filter_faces(source_faces, target_faces))

		if target_face:
			return [ source_face ], [ target_face ]

	if state_manager.get_item('face_selector_mode') == 'reference':
		__source_faces__ = []
		match_faces = []

		for (source_frame_index, source_face_position), reference_faces in collect_reference_face_set(reference_vision_frames).items():
			source_frame_faces = get_static_faces(source_vision_frames[source_frame_index:source_frame_index + 1])
			source_frame_faces = sort_faces_by_order(source_frame_faces, 'large-small')
			source_face = get_one_face(source_frame_faces, source_face_position)

			for target_face in target_faces:
				if find_match_faces(reference_faces, [ target_face ], state_manager.get_item('reference_face_distance')):
					__source_faces__.append(source_face)
					match_faces.append(target_face)

		return __source_faces__, match_faces

	return [], []


def extract_one_face(vision_frames : List[VisionFrame]) -> Optional[Face]:
	faces = []

	if vision_frames:
		for vision_frame in vision_frames:
			temp_faces = get_static_faces([ vision_frame ])
			temp_faces = sort_faces_by_order(temp_faces, 'large-small')

			if temp_faces:
				faces.append(get_first(temp_faces))

	return average_face_identity(faces)


def collect_reference_face_set(reference_vision_frames : List[VisionFrame]) -> ReferenceFaceSet:
	reference_face_set : ReferenceFaceSet = {}

	for reference_vision_frame, reference_face_map in zip(reference_vision_frames, state_manager.get_item('reference_face_maps')):
		source_frame_index, source_face_position, _, reference_face_position = reference_face_map
		reference_faces = get_static_faces([ reference_vision_frame ])
		reference_faces = sort_faces_by_order(reference_faces, 'large-small')
		reference_face = get_one_face(reference_faces, reference_face_position)

		if reference_face:
			reference_face_set.setdefault((source_frame_index, source_face_position), []).append(reference_face)

	return reference_face_set


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


def sort_and_filter_faces(source_faces : List[Face], target_faces : List[Face]) -> List[Face]:
	if target_faces:
		if state_manager.get_item('face_selector_order'):
			target_faces = sort_faces_by_order(target_faces, state_manager.get_item('face_selector_order'))

		face_selector_gender = state_manager.get_item('face_selector_gender')
		face_selector_race = state_manager.get_item('face_selector_race')

		if source_faces and face_selector_gender == 'auto' or face_selector_race == 'auto':
			source_face = get_first(sort_faces_by_order(source_faces, 'large-small'))

			if source_face:
				if face_selector_gender == 'auto':
					face_selector_gender = source_face.gender
				if face_selector_race == 'auto':
					face_selector_race = source_face.race

		if face_selector_gender in facefusion.choices.genders:
			target_faces = filter_faces_by_gender(target_faces, face_selector_gender)

		if face_selector_race in facefusion.choices.races:
			target_faces = filter_faces_by_race(target_faces, face_selector_race)

		if state_manager.get_item('face_selector_age_start') or state_manager.get_item('face_selector_age_end'):
			target_faces = filter_faces_by_age(target_faces, state_manager.get_item('face_selector_age_start'), state_manager.get_item('face_selector_age_end'))

	return target_faces


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
