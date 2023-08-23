import threading
from typing import Any, Optional, List
import insightface
import numpy

import facefusion.globals
from facefusion.typing import Frame, Face, FaceAnalyserDirection, FaceAnalyserAge, FaceAnalyserGender

FACE_ANALYSER = None
THREAD_LOCK = threading.Lock()

class FaceAnalyserSingleton:
    _instance = None

    def __new__(cls):
        with THREAD_LOCK:
            if cls._instance is None:
                cls._instance = super(FaceAnalyserSingleton, cls).__new__(cls)
                cls._instance.init_face_analyser()
        return cls._instance

    def init_face_analyser(self):
        self.face_analyser = insightface.app.FaceAnalysis(name='buffalo_l', providers=facefusion.globals.execution_providers)
        self.face_analyser.prepare(ctx_id=0)

def get_face_analyser() -> Any:
    return FaceAnalyserSingleton().face_analyser

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

def sort_by_direction(faces: List[Face], direction: FaceAnalyserDirection) -> List[Face]:
    sorting_functions = {
        'left-right': lambda face: face['bbox'][0],
        'right-left': lambda face: -face['bbox'][0],
        'top-bottom': lambda face: face['bbox'][1],
        'bottom-top': lambda face: -face['bbox'][1],
        'small-large': lambda face: (face['bbox'][2] - face['bbox'][0]) * (face['bbox'][3] - face['bbox'][1]),
        'large-small': lambda face: -(face['bbox'][2] - face['bbox'][0]) * (face['bbox'][3] - face['bbox'][1])
    }
    
    if direction in sorting_functions:
        return sorted(faces, key=sorting_functions[direction])
    return faces

def filter_by_age(faces: List[Face], age: FaceAnalyserAge) -> List[Face]:
    age_ranges = {
        'child': (0, 13),
        'teen': (13, 19),
        'adult': (19, 60),
        'senior': (60, float('inf'))
    }
    min_age, max_age = age_ranges[age]
    return [face for face in faces if min_age <= face['age'] < max_age]

def filter_by_gender(faces: List[Face], gender: FaceAnalyserGender) -> List[Face]:
    gender_mapping = {
        'male': 1,
        'female': 0
    }
    target_gender = gender_mapping[gender]
    return [face for face in faces if face['gender'] == target_gender]

def get_faces_total(frame : Frame) -> int:
	return len(get_many_faces(frame))
