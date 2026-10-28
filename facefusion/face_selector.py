from typing import List, Optional, Tuple

import numpy

import facefusion.choices
from facefusion import state_manager
from facefusion.common_helper import get_first, get_middle
from facefusion.face_creator import average_face_identity, get_one_face, get_static_faces
from facefusion.face_tracker import track_faces
from facefusion.types import Face, FacePointer, FaceSelectorMap, FaceSelectorOrder, Gender, Map, Race, Score, VisionFrame


def select_faces(reference_vision_frames : List[VisionFrame], source_vision_frames : List[VisionFrame], target_vision_frames : List[VisionFrame]) -> Tuple[List[Face], List[Face]]:
	source_faces = get_static_faces(source_vision_frames)

	if state_manager.get_item('face_tracker_score') > 0:
		target_faces = track_faces(target_vision_frames, state_manager.get_item('face_tracker_score'))
	else:
		target_faces = get_static_faces([ get_middle(target_vision_frames) ])

	face_selector_maps = decode_face_selector_maps(state_manager.get_item('face_selector_maps'))

	if state_manager.get_item('face_selector_mode') == 'many':
		source_face = extract_source_face(source_vision_frames, collect_source_faces(face_selector_maps))
		__source_faces__ : List[Face] = []
		match_faces : List[Face] = []

		for target_face in sort_and_filter_faces(source_faces, target_faces):
			__source_faces__.append(source_face)
			match_faces.append(target_face)

		return __source_faces__, match_faces

	if state_manager.get_item('face_selector_mode') == 'one':
		source_face = extract_source_face(source_vision_frames, collect_source_faces(face_selector_maps))
		target_face = get_one_face(sort_and_filter_faces(source_faces, target_faces))

		if target_face:
			return [ source_face ], [ target_face ]

	if state_manager.get_item('face_selector_mode') == 'reference':
		group_source_faces : List[Optional[Face]] = []
		group_reference_faces : List[List[Face]] = []
		__source_faces__ = []
		match_faces = []

		for face_selector_map in face_selector_maps:
			group_source_faces.append(extract_source_face(source_vision_frames, face_selector_map.get('source_faces')))
			group_reference_faces.append(extract_reference_faces(reference_vision_frames, face_selector_map.get('reference_faces')))
			reference_vision_frames = reference_vision_frames[len(face_selector_map.get('reference_faces')):]

		for target_face in target_faces:
			group_index = find_match_group_index(group_reference_faces, target_face, state_manager.get_item('reference_face_distance'))

			if isinstance(group_index, int):
				__source_faces__.append(group_source_faces[group_index])
				match_faces.append(target_face)

		return __source_faces__, match_faces

	return [], []


def decode_face_selector_maps(face_selector_maps : Optional[List[Map]]) -> List[FaceSelectorMap]:
	temp_face_selector_maps : List[FaceSelectorMap] = []

	if face_selector_maps:
		for face_selector_map in face_selector_maps:
			__face_selector_map__ = decode_face_selector_map(face_selector_map)

			if __face_selector_map__.get('source_faces') or __face_selector_map__.get('reference_faces'):
				temp_face_selector_maps.append(__face_selector_map__)

	return temp_face_selector_maps


def decode_face_selector_map(face_selector_map : Map) -> FaceSelectorMap:
	source_faces : List[FacePointer] = []
	reference_faces : List[FacePointer] = []
	faces = source_faces

	for face_selector_value in face_selector_map.split():
		frame_index, _, face_position = face_selector_value.partition(':')

		if face_selector_value == 'to':
			faces = reference_faces

		if frame_index.isdecimal() and face_position.isdecimal():
			faces.append(
			{
				'frame_index': int(frame_index),
				'face_position': int(face_position)
			})

	return\
	{
		'source_faces': source_faces,
		'reference_faces': reference_faces
	}


def collect_source_faces(face_selector_maps : List[FaceSelectorMap]) -> List[FacePointer]:
	source_faces : List[FacePointer] = []

	for face_selector_map in face_selector_maps:
		source_faces.extend(face_selector_map.get('source_faces'))

	return source_faces


def extract_source_face(source_vision_frames : List[VisionFrame], source_faces : List[FacePointer]) -> Optional[Face]:
	faces = []

	if source_faces:
		for source_face in source_faces:
			frame_index = source_face.get('frame_index')
			temp_faces = get_static_faces(source_vision_frames[frame_index:frame_index + 1])
			temp_faces = sort_faces_by_order(temp_faces, 'large-small')
			face = get_one_face(temp_faces, source_face.get('face_position'))

			if face:
				faces.append(face)

		return average_face_identity(faces)

	for source_vision_frame in source_vision_frames:
		temp_faces = get_static_faces([ source_vision_frame ])
		temp_faces = sort_faces_by_order(temp_faces, 'large-small')

		if temp_faces:
			faces.append(get_first(temp_faces))

	return average_face_identity(faces)


def extract_reference_faces(reference_vision_frames : List[VisionFrame], reference_faces : List[FacePointer]) -> List[Face]:
	faces = []

	for reference_face, reference_vision_frame in zip(reference_faces, reference_vision_frames):
		temp_faces = get_static_faces([ reference_vision_frame ])
		temp_faces = sort_faces_by_order(temp_faces, 'large-small')
		face = get_one_face(temp_faces, reference_face.get('face_position'))

		if face:
			faces.append(face)

	return faces


def find_match_group_index(group_reference_faces : List[List[Face]], target_face : Face, face_distance : float) -> Optional[int]:
	group_index = None
	match_face_distance = face_distance

	for index, reference_faces in enumerate(group_reference_faces):
		for reference_face in reference_faces:
			current_face_distance = calculate_face_distance(target_face, reference_face)
			current_face_distance = float(numpy.interp(current_face_distance, [ 0, 2 ], [ 0, 1 ]))

			if current_face_distance < match_face_distance:
				match_face_distance = current_face_distance
				group_index = index

	return group_index


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
