import threading
from typing import Any, Optional, List
import insightface
import numpy

import facefusion.globals
from facefusion.typing import Frame, Face, FaceAnalyserDirection, FaceAnalyserAge, FaceAnalyserGender

FACE_ANALYSER = None
THREAD_LOCK = threading.Lock()


def get_face_analyser() -> Any:
	global FACE_ANALYSER

	with THREAD_LOCK:
		if FACE_ANALYSER is None:
			FACE_ANALYSER = insightface.app.FaceAnalysis(name = 'buffalo_l', providers = facefusion.globals.execution_providers)
			FACE_ANALYSER.prepare(ctx_id = 0)
	return FACE_ANALYSER


def clear_face_analyser() -> Any:
	global FACE_ANALYSER

	FACE_ANALYSER = None


def get_one_face(frame : Frame, position : int = 0) -> Optional[Face]:
	many_faces = get_many_faces(frame)
	if many_faces:
		try:
			return many_faces[position]
		except IndexError:
			return many_faces[-1]
	return None


def get_many_faces(frame : Frame) -> List[Face]:
	try:
		faces = get_face_analyser().get(frame)
		if facefusion.globals.face_analyser_direction:
			faces = sort_by_direction(faces, facefusion.globals.face_analyser_direction)
		if facefusion.globals.face_analyser_age:
			faces = filter_by_age(faces, facefusion.globals.face_analyser_age)
		if facefusion.globals.face_analyser_gender:
			faces = filter_by_gender(faces, facefusion.globals.face_analyser_gender)
		return faces
	except (AttributeError, ValueError):
		return []


def find_similar_faces(frame : Frame, reference_face : Face, face_distance : float) -> List[Face]:
	many_faces = get_many_faces(frame)
	similar_faces = []
	if many_faces:
		for face in many_faces:
			if hasattr(face, 'normed_embedding') and hasattr(reference_face, 'normed_embedding'):
				current_face_distance = numpy.sum(numpy.square(face.normed_embedding - reference_face.normed_embedding))
				if current_face_distance < face_distance:
					similar_faces.append(face)
	return similar_faces


def sort_by_direction(faces : List[Face], direction : FaceAnalyserDirection) -> List[Face]:
	if direction == 'left-right':
		return sorted(faces, key = lambda face: face['bbox'][0])
	if direction == 'right-left':
		return sorted(faces, key = lambda face: face['bbox'][0], reverse = True)
	if direction == 'top-bottom':
		return sorted(faces, key = lambda face: face['bbox'][1])
	if direction == 'bottom-top':
		return sorted(faces, key = lambda face: face['bbox'][1], reverse = True)
	if direction == 'small-large':
		return sorted(faces, key = lambda face: (face['bbox'][2] - face['bbox'][0]) * (face['bbox'][3] - face['bbox'][1]))
	if direction == 'large-small':
		return sorted(faces, key = lambda face: (face['bbox'][2] - face['bbox'][0]) * (face['bbox'][3] - face['bbox'][1]), reverse = True)
	return faces


def filter_by_age(faces : List[Face], age : FaceAnalyserAge) -> List[Face]:
	filter_faces = []
	for face in faces:
		if face['age'] < 13 and age == 'child':
			filter_faces.append(face)
		elif face['age'] < 19 and age == 'teen':
			filter_faces.append(face)
		elif face['age'] < 60 and age == 'adult':
			filter_faces.append(face)
		elif face['age'] > 59 and age == 'senior':
			filter_faces.append(face)
	return filter_faces


def filter_by_gender(faces : List[Face], gender : FaceAnalyserGender) -> List[Face]:
	filter_faces = []
	for face in faces:
		if face['gender'] == 1 and gender == 'male':
			filter_faces.append(face)
		if face['gender'] == 0 and gender == 'female':
			filter_faces.append(face)
	return filter_faces


def get_faces_total(frame : Frame) -> int:
	return len(get_many_faces(frame))
