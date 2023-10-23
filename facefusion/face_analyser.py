from typing import Any, Optional, List, Dict, Tuple
import threading
import cv2
import numpy
import onnxruntime

import facefusion.globals
from facefusion.face_cache import get_faces_cache, set_faces_cache
from facefusion.face_helper import warp_face
from facefusion.typing import Frame, Face, FaceAnalyserDirection, FaceAnalyserAge, FaceAnalyserGender, ModelValue, Kps, Embedding
from facefusion.utilities import resolve_relative_path, conditional_download
from facefusion.vision import resize_frame_dimension
from facefusion.processors.frame import globals as frame_processors_globals

FACE_ANALYSER = None
THREAD_SEMAPHORE : threading.Semaphore = threading.Semaphore()
THREAD_LOCK : threading.Lock = threading.Lock()
MODELS : Dict[str, ModelValue] =\
{
	'face_recognition_arcface_ghost':
	{
		'url': 'https://github.com/harisreedhar/Face-Swappers-ONNX/releases/download/ghost/ghost_arcface_backbone.onnx',
		'path': resolve_relative_path('../.assets/models/ghost_arcface_backbone.onnx')
	},
	'face_recognition_arcface_inswapper':
	{
		'url': 'https://huggingface.co/bluefoxcreation/insightface-retinaface-arcface-model/resolve/main/w600k_r50.onnx',
		'path': resolve_relative_path('../.assets/models/w600k_r50.onnx')
	},
	'face_recognition_arcface_simswap':
	{
		'url': 'https://github.com/harisreedhar/Face-Swappers-ONNX/releases/download/simswap/simswap_arcface_backbone.onnx',
		'path': resolve_relative_path('../.assets/models/simswap_arcface_backbone.onnx')
	},
	'face_detection_yunet':
	{
		'url': 'https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx',
		'path': resolve_relative_path('../.assets/models/face_detection_yunet_2023mar.onnx')
	},
	'gender_age':
	{
		'url': 'https://huggingface.co/facefusion/buffalo_l/resolve/main/genderage.onnx',
		'path': resolve_relative_path('../.assets/models/genderage.onnx')
	}
}


def get_face_analyser() -> Any:
	global FACE_ANALYSER

	with THREAD_LOCK:
		if FACE_ANALYSER is None:
			if frame_processors_globals.face_swapper_model == 'ghost_unet_1_block' or frame_processors_globals.face_swapper_model == 'ghost_unet_2_block' or frame_processors_globals.face_swapper_model == 'ghost_unet_3_block':
				face_recognition_model_path = MODELS.get('face_recognition_arcface_inswapper').get('path')
			if frame_processors_globals.face_swapper_model == 'inswapper_128' or frame_processors_globals.face_swapper_model == 'inswapper_128_fp16':
				face_recognition_model_path = MODELS.get('face_recognition_arcface_inswapper').get('path')
			if frame_processors_globals.face_swapper_model == 'simswap_244' or frame_processors_globals.face_swapper_model == 'simswap_512_beta':
				face_recognition_model_path = MODELS.get('face_recognition_arcface_simswap').get('path')
			FACE_ANALYSER =\
			{
				'face_detector': cv2.FaceDetectorYN.create(MODELS.get('face_detection_yunet').get('path'), None, (0, 0)),
				'face_recognition': onnxruntime.InferenceSession(face_recognition_model_path, providers = facefusion.globals.execution_providers),
				'gender_age': onnxruntime.InferenceSession(MODELS.get('gender_age').get('path'), providers = facefusion.globals.execution_providers),
			}
	return FACE_ANALYSER


def clear_face_analyser() -> Any:
	global FACE_ANALYSER

	FACE_ANALYSER = None


def pre_check() -> bool:
	if not facefusion.globals.skip_download:
		download_directory_path = resolve_relative_path('../.assets/models')
		model_urls =\
		[
			MODELS.get('face_recognition_arcface_ghost').get('url'),
			MODELS.get('face_recognition_arcface_inswapper').get('url'),
			MODELS.get('face_recognition_arcface_simswap').get('url'),
			MODELS.get('face_detection_yunet').get('url'),
			MODELS.get('gender_age').get('url')
		]
		conditional_download(download_directory_path, model_urls)
	return True


def extract_faces(frame : Frame) -> List[Face]:
	face_detector = get_face_analyser().get('face_detector')
	faces: List[Face] = []
	temp_frame = resize_frame_dimension(frame, 1024, 1024)
	temp_frame_height, temp_frame_width, _ = temp_frame.shape
	frame_height, frame_width, _ = frame.shape
	ratio_height = frame_height / temp_frame_height
	ratio_width = frame_width / temp_frame_width
	face_detector.setScoreThreshold(0.5)
	face_detector.setNMSThreshold(0.5)
	face_detector.setTopK(100)
	face_detector.setInputSize((temp_frame_width, temp_frame_height))
	with THREAD_SEMAPHORE:
		_, detections = face_detector.detect(temp_frame)
	if detections.any():
		for detection in detections:
			bbox =\
			[
				detection[0:4][0] * ratio_width,
				detection[0:4][1] * ratio_height,
				(detection[0:4][0] + detection[0:4][2]) * ratio_width,
				(detection[0:4][1] + detection[0:4][3]) * ratio_height
			]
			kps = (detection[4:14].reshape((5, 2)) * [[ ratio_width, ratio_height ]])
			score = detection[14]
			embedding = calc_embedding(frame, kps)
			normed_embedding = embedding / numpy.linalg.norm(embedding)
			gender, age = detect_gender_age(frame, kps)
			faces.append(Face(
				bbox = bbox,
				kps = kps,
				score = score,
				embedding = embedding,
				normed_embedding = normed_embedding,
				gender = gender,
				age = age
			))
	return faces


def calc_embedding(temp_frame : Frame, kps : Kps) -> Embedding:
	face_recognition = get_face_analyser().get('face_recognition')
	crop_frame, matrix = warp_face(temp_frame, kps, 'arcface', (112, 112))
	crop_frame = crop_frame.astype(numpy.float32) / 127.5 - 1
	crop_frame = crop_frame[:, :, ::-1].transpose(2, 0, 1)
	crop_frame = numpy.expand_dims(crop_frame, axis = 0)
	embedding = face_recognition.run(None,
	{
		face_recognition.get_inputs()[0].name: crop_frame
	})[0]
	embedding = embedding.ravel()
	return embedding


def detect_gender_age(frame : Frame, kps : Kps) -> Tuple[int, int]:
	gender_age = get_face_analyser().get('gender_age')
	crop_frame, affine_matrix = warp_face(frame, kps, 'arcface', (96, 96))
	crop_frame = numpy.expand_dims(crop_frame, axis = 0).transpose(0, 3, 1, 2).astype(numpy.float32)
	prediction = gender_age.run(None,
	{
		gender_age.get_inputs()[0].name: crop_frame
	})[0][0]
	gender = int(numpy.argmax(prediction[:2]))
	age = int(numpy.round(prediction[2] * 100))
	return gender, age


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
				current_face_distance = 1 - numpy.dot(face.normed_embedding, reference_face.normed_embedding)
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
