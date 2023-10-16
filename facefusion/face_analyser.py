from typing import Any, Optional, List, Dict
import threading
import dlib
import numpy
import onnxruntime

import facefusion.globals
from facefusion.face_cache import get_faces_cache, set_faces_cache
from facefusion.face_helper import warp_face
from facefusion.typing import Frame, Face, FaceAnalyserDirection, FaceAnalyserAge, FaceAnalyserGender, ModelValue, Kps, Embedding
from facefusion.utilities import resolve_relative_path, conditional_download

FACE_ANALYSER = None
THREAD_LOCK : threading.Lock = threading.Lock()
MODELS : Dict[str, ModelValue] =\
{
	'arcface':
	{
		'url': 'https://huggingface.co/bluefoxcreation/insightface-retinaface-arcface-model/resolve/main/w600k_r50.onnx',
		'path': resolve_relative_path('../.assets/models/w600k_r50.onnx')
	},
	'shape_predictor':
	{
		'url': 'https://github.com/ageitgey/face_recognition_models/raw/master/face_recognition_models/models/shape_predictor_68_face_landmarks.dat',
		'path': resolve_relative_path('../.assets/models/shape_predictor_68_face_landmarks.dat')
	},
	'face_recognition':
	{
		'url': 'https://github.com/ageitgey/face_recognition_models/raw/master/face_recognition_models/models/dlib_face_recognition_resnet_model_v1.dat',
		'path': resolve_relative_path('../.assets/models/dlib_face_recognition_resnet_model_v1.dat')
	}
}


def get_face_analyser() -> Any:
	global FACE_ANALYSER

	with THREAD_LOCK:
		if FACE_ANALYSER is None:
			FACE_ANALYSER =\
			{
				'face_recognition_arcface': onnxruntime.InferenceSession(MODELS.get('arcface').get('path'), None, providers = facefusion.globals.execution_providers),
				'frontal_face_detector': dlib.get_frontal_face_detector(),
				'shape_predictor': dlib.shape_predictor(MODELS.get('shape_predictor').get('path')),
			}
	return FACE_ANALYSER


def clear_face_analyser() -> Any:
	global FACE_ANALYSER

	FACE_ANALYSER = None


def pre_check() -> bool:
	if not facefusion.globals.skip_download:
		download_directory_path = resolve_relative_path('../.assets/models')
		model_urls = [ MODELS.get('arcface').get('url'), MODELS.get('shape_predictor').get('url'), MODELS.get('face_recognition').get('url') ]
		conditional_download(download_directory_path, model_urls)
	return True


def extract_faces(frame : Frame) -> List[Face]:
	face_analyser = get_face_analyser()
	frontal_face_detector = face_analyser.get('frontal_face_detector')
	faces : List[Face] = []
	for temp_rectangle in frontal_face_detector(frame):
		bbox = numpy.array([ temp_rectangle.left(), temp_rectangle.top(), temp_rectangle.right(), temp_rectangle.bottom() ])
		kps = create_kps(frame, temp_rectangle)
		embedding = create_embedding(frame, kps)
		normed_embedding = numpy.linalg.norm(embedding)
		faces.append(Face(
			bbox = bbox,
			kps = kps,
			embedding = embedding,
			normed_embedding = normed_embedding,
			gender = 0,
			age = 0
		))
	return faces


def create_kps(frame : Frame, temp_rectangle : dlib.rectangle) -> Kps:
	face_analyser = get_face_analyser()
	shape_predictor = face_analyser.get('shape_predictor')
	shape = shape_predictor(frame, temp_rectangle)
	left_eye = numpy.mean(shape.parts()[36:42], axis = 0)
	right_eye = numpy.mean(shape.parts()[42:48], axis = 0)
	nose = shape.part(30)
	left_mouth = shape.part(48)
	right_mouth = shape.part(54)
	landmarks = [ left_eye, right_eye, nose, left_mouth, right_mouth ]
	kps = numpy.array([[ landmark.x, landmark.y ] for landmark in landmarks ]).astype(numpy.float32)
	return kps


def create_embedding(temp_frame : Frame, kps : Kps) -> Embedding:
	face_analyser = get_face_analyser()
	face_recognition = face_analyser.get('face_recognition_arcface')
	crop_frame, matrix = warp_face(temp_frame, kps, 'arcface', (112, 112))
	crop_frame = crop_frame.astype(numpy.float32) / 127.5 - 1
	crop_frame = crop_frame[:, :, ::-1].transpose(2, 0, 1)
	crop_frame = numpy.expand_dims(crop_frame, axis = 0)
	embedding = face_recognition.run(None,
	{
		face_recognition.get_inputs()[0].name: crop_frame
	})[0]
	return embedding.ravel()


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
		faces_cache = get_faces_cache(frame)
		if faces_cache:
			faces = faces_cache
		else:
			faces = extract_faces(frame)
			set_faces_cache(frame, faces)
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
		return sorted(faces, key = lambda face: face.bbox[0])
	if direction == 'right-left':
		return sorted(faces, key = lambda face: face.bbox[0], reverse = True)
	if direction == 'top-bottom':
		return sorted(faces, key = lambda face: face.bbox[1])
	if direction == 'bottom-top':
		return sorted(faces, key = lambda face: face.bbox[1], reverse = True)
	if direction == 'small-large':
		return sorted(faces, key = lambda face: (face.bbox[2] - face.bbox[0]) * (face.bbox[3] - face.bbox[1]))
	if direction == 'large-small':
		return sorted(faces, key = lambda face: (face.bbox[2] - face.bbox[0]) * (face.bbox[3] - face.bbox[1]), reverse = True)
	return faces


def filter_by_age(faces : List[Face], age : FaceAnalyserAge) -> List[Face]:
	filter_faces = []
	for face in faces:
		if face.age < 13 and age == 'child':
			filter_faces.append(face)
		elif face.age < 19 and age == 'teen':
			filter_faces.append(face)
		elif face.age < 60 and age == 'adult':
			filter_faces.append(face)
		elif face.age > 59 and age == 'senior':
			filter_faces.append(face)
	return filter_faces


def filter_by_gender(faces : List[Face], gender : FaceAnalyserGender) -> List[Face]:
	filter_faces = []
	for face in faces:
		if face.gender == 1 and gender == 'male':
			filter_faces.append(face)
		if face.gender == 0 and gender == 'female':
			filter_faces.append(face)
	return filter_faces
