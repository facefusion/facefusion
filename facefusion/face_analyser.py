from typing import Any, Optional, List, Tuple
import threading
import cv2
import numpy
import onnxruntime

import facefusion.globals
from facefusion.download import conditional_download
from facefusion.face_store import get_static_faces, set_static_faces
from facefusion.face_helper import warp_face, create_static_anchors, distance_to_kps, distance_to_bbox, apply_nms
from facefusion.filesystem import resolve_relative_path
from facefusion.typing import Frame, Face, FaceSet, FaceAnalyserOrder, FaceAnalyserAge, FaceAnalyserGender, ModelSet, Bbox, Kps, Score, Embedding
from facefusion.vision import resize_frame_dimension

FACE_ANALYSER = None
THREAD_SEMAPHORE : threading.Semaphore = threading.Semaphore()
THREAD_LOCK : threading.Lock = threading.Lock()
MODELS : ModelSet =\
{
	'face_detector_retinaface':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/retinaface_10g.onnx',
		'path': resolve_relative_path('../.assets/models/retinaface_10g.onnx')
	},
	'face_detector_yunet':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/yunet_2023mar.onnx',
		'path': resolve_relative_path('../.assets/models/yunet_2023mar.onnx')
	},
	'face_recognizer_arcface_blendswap':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/arcface_w600k_r50.onnx',
		'path': resolve_relative_path('../.assets/models/arcface_w600k_r50.onnx')
	},
	'face_recognizer_arcface_inswapper':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/arcface_w600k_r50.onnx',
		'path': resolve_relative_path('../.assets/models/arcface_w600k_r50.onnx')
	},
	'face_recognizer_arcface_simswap':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/arcface_simswap.onnx',
		'path': resolve_relative_path('../.assets/models/arcface_simswap.onnx')
	},
	'gender_age':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/gender_age.onnx',
		'path': resolve_relative_path('../.assets/models/gender_age.onnx')
	}
}


def get_face_analyser() -> Any:
	global FACE_ANALYSER

	with THREAD_LOCK:
		if FACE_ANALYSER is None:
			if facefusion.globals.face_detector_model == 'retinaface':
				face_detector = onnxruntime.InferenceSession(MODELS.get('face_detector_retinaface').get('path'), providers = facefusion.globals.execution_providers)
			if facefusion.globals.face_detector_model == 'yunet':
				face_detector = cv2.FaceDetectorYN.create(MODELS.get('face_detector_yunet').get('path'), '', (0, 0))
			if facefusion.globals.face_recognizer_model == 'arcface_blendswap':
				face_recognizer = onnxruntime.InferenceSession(MODELS.get('face_recognizer_arcface_blendswap').get('path'), providers = facefusion.globals.execution_providers)
			if facefusion.globals.face_recognizer_model == 'arcface_inswapper':
				face_recognizer = onnxruntime.InferenceSession(MODELS.get('face_recognizer_arcface_inswapper').get('path'), providers = facefusion.globals.execution_providers)
			if facefusion.globals.face_recognizer_model == 'arcface_simswap':
				face_recognizer = onnxruntime.InferenceSession(MODELS.get('face_recognizer_arcface_simswap').get('path'), providers = facefusion.globals.execution_providers)
			gender_age = onnxruntime.InferenceSession(MODELS.get('gender_age').get('path'), providers = facefusion.globals.execution_providers)
			FACE_ANALYSER =\
			{
				'face_detector': face_detector,
				'face_recognizer': face_recognizer,
				'gender_age': gender_age
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
			MODELS.get('face_detector_retinaface').get('url'),
			MODELS.get('face_detector_yunet').get('url'),
			MODELS.get('face_recognizer_arcface_inswapper').get('url'),
			MODELS.get('face_recognizer_arcface_simswap').get('url'),
			MODELS.get('gender_age').get('url')
		]
		conditional_download(download_directory_path, model_urls)
	return True


def extract_faces(frame: Frame) -> List[Face]:
	face_detector_width, face_detector_height = map(int, facefusion.globals.face_detector_size.split('x'))
	frame_height, frame_width, _ = frame.shape
	temp_frame = resize_frame_dimension(frame, face_detector_width, face_detector_height)
	temp_frame_height, temp_frame_width, _ = temp_frame.shape
	ratio_height = frame_height / temp_frame_height
	ratio_width = frame_width / temp_frame_width
	if facefusion.globals.face_detector_model == 'retinaface':
		bbox_list, kps_list, score_list = detect_with_retinaface(temp_frame, temp_frame_height, temp_frame_width, face_detector_height, face_detector_width, ratio_height, ratio_width)
		return create_faces(frame, bbox_list, kps_list, score_list)
	elif facefusion.globals.face_detector_model == 'yunet':
		bbox_list, kps_list, score_list = detect_with_yunet(temp_frame, temp_frame_height, temp_frame_width, ratio_height, ratio_width)
		return create_faces(frame, bbox_list, kps_list, score_list)
	return []


def detect_with_retinaface(temp_frame : Frame, temp_frame_height : int, temp_frame_width : int, face_detector_height : int, face_detector_width : int, ratio_height : float, ratio_width : float) -> Tuple[List[Bbox], List[Kps], List[Score]]:
	face_detector = get_face_analyser().get('face_detector')
	bbox_list = []
	kps_list = []
	score_list = []
	feature_strides = [ 8, 16, 32 ]
	feature_map_channel = 3
	anchor_total = 2
	prepare_frame = numpy.zeros((face_detector_height, face_detector_width, 3))
	prepare_frame[:temp_frame_height, :temp_frame_width, :] = temp_frame
	temp_frame = (prepare_frame - 127.5) / 128.0
	temp_frame = numpy.expand_dims(temp_frame.transpose(2, 0, 1), axis = 0).astype(numpy.float32)
	with THREAD_SEMAPHORE:
		detections = face_detector.run(None,
		{
			face_detector.get_inputs()[0].name: temp_frame
		})
	for index, feature_stride in enumerate(feature_strides):
		keep_indices = numpy.where(detections[index] >= facefusion.globals.face_detector_score)[0]
		if keep_indices.any():
			stride_height = face_detector_height // feature_stride
			stride_width = face_detector_width // feature_stride
			anchors = create_static_anchors(feature_stride, anchor_total, stride_height, stride_width)
			bbox_raw = (detections[index + feature_map_channel] * feature_stride)
			kps_raw = detections[index + feature_map_channel * 2] * feature_stride
			for bbox in distance_to_bbox(anchors, bbox_raw)[keep_indices]:
				bbox_list.append(numpy.array(
				[
					bbox[0] * ratio_width,
					bbox[1] * ratio_height,
					bbox[2] * ratio_width,
					bbox[3] * ratio_height
				]))
			for kps in distance_to_kps(anchors, kps_raw)[keep_indices]:
				kps_list.append(kps * [ ratio_width, ratio_height ])
			for score in detections[index][keep_indices]:
				score_list.append(score[0])
	return bbox_list, kps_list, score_list


def detect_with_yunet(temp_frame : Frame, temp_frame_height : int, temp_frame_width : int, ratio_height : float, ratio_width : float) -> Tuple[List[Bbox], List[Kps], List[Score]]:
	face_detector = get_face_analyser().get('face_detector')
	face_detector.setInputSize((temp_frame_width, temp_frame_height))
	face_detector.setScoreThreshold(facefusion.globals.face_detector_score)
	bbox_list = []
	kps_list = []
	score_list = []
	with THREAD_SEMAPHORE:
		_, detections = face_detector.detect(temp_frame)
	if detections.any():
		for detection in detections:
			bbox_list.append(numpy.array(
			[
				detection[0] * ratio_width,
				detection[1] * ratio_height,
				(detection[0] + detection[2]) * ratio_width,
				(detection[1] + detection[3]) * ratio_height
			]))
			kps_list.append(detection[4:14].reshape((5, 2)) * [ ratio_width, ratio_height])
			score_list.append(detection[14])
	return bbox_list, kps_list, score_list


def create_faces(frame : Frame, bbox_list : List[Bbox], kps_list : List[Kps], score_list : List[Score]) -> List[Face]:
	faces = []
	if facefusion.globals.face_detector_score > 0:
		sort_indices = numpy.argsort(-numpy.array(score_list))
		bbox_list = [ bbox_list[index] for index in sort_indices ]
		kps_list = [ kps_list[index] for index in sort_indices ]
		score_list = [ score_list[index] for index in sort_indices ]
		keep_indices = apply_nms(bbox_list, 0.4)
		for index in keep_indices:
			bbox = bbox_list[index]
			kps = kps_list[index]
			score = score_list[index]
			embedding, normed_embedding = calc_embedding(frame, kps)
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


def calc_embedding(temp_frame : Frame, kps : Kps) -> Tuple[Embedding, Embedding]:
	face_recognizer = get_face_analyser().get('face_recognizer')
	crop_frame, matrix = warp_face(temp_frame, kps, 'arcface_112_v2', (112, 112))
	crop_frame = crop_frame.astype(numpy.float32) / 127.5 - 1
	crop_frame = crop_frame[:, :, ::-1].transpose(2, 0, 1)
	crop_frame = numpy.expand_dims(crop_frame, axis = 0)
	embedding = face_recognizer.run(None,
	{
		face_recognizer.get_inputs()[0].name: crop_frame
	})[0]
	embedding = embedding.ravel()
	normed_embedding = embedding / numpy.linalg.norm(embedding)
	return embedding, normed_embedding


def detect_gender_age(frame : Frame, kps : Kps) -> Tuple[int, int]:
	gender_age = get_face_analyser().get('gender_age')
	crop_frame, affine_matrix = warp_face(frame, kps, 'arcface_112_v2', (96, 96))
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


def get_average_face(frames : List[Frame], position : int = 0) -> Optional[Face]:
	average_face = None
	faces = []
	embedding_list = []
	normed_embedding_list = []
	for frame in frames:
		face = get_one_face(frame, position)
		if face:
			faces.append(face)
			embedding_list.append(face.embedding)
			normed_embedding_list.append(face.normed_embedding)
	if faces:
		average_face = Face(
			bbox = faces[0].bbox,
			kps = faces[0].kps,
			score = faces[0].score,
			embedding = numpy.mean(embedding_list, axis = 0),
			normed_embedding = numpy.mean(normed_embedding_list, axis = 0),
			gender = faces[0].gender,
			age = faces[0].age
		)
	return average_face


def get_many_faces(frame : Frame) -> List[Face]:
	try:
		faces_cache = get_static_faces(frame)
		if faces_cache:
			faces = faces_cache
		else:
			faces = extract_faces(frame)
			set_static_faces(frame, faces)
		if facefusion.globals.face_analyser_order:
			faces = sort_by_order(faces, facefusion.globals.face_analyser_order)
		if facefusion.globals.face_analyser_age:
			faces = filter_by_age(faces, facefusion.globals.face_analyser_age)
		if facefusion.globals.face_analyser_gender:
			faces = filter_by_gender(faces, facefusion.globals.face_analyser_gender)
		return faces
	except (AttributeError, ValueError):
		return []


def find_similar_faces(frame : Frame, reference_faces : FaceSet, face_distance : float) -> List[Face]:
	similar_faces : List[Face] = []
	many_faces = get_many_faces(frame)

	if reference_faces:
		for reference_set in reference_faces:
			if not similar_faces:
				for reference_face in reference_faces[reference_set]:
					for face in many_faces:
						if compare_faces(face, reference_face, face_distance):
							similar_faces.append(face)
	return similar_faces


def compare_faces(face : Face, reference_face : Face, face_distance : float) -> bool:
	if hasattr(face, 'normed_embedding') and hasattr(reference_face, 'normed_embedding'):
		current_face_distance = 1 - numpy.dot(face.normed_embedding, reference_face.normed_embedding)
		return current_face_distance < face_distance
	return False


def sort_by_order(faces : List[Face], order : FaceAnalyserOrder) -> List[Face]:
	if order == 'left-right':
		return sorted(faces, key = lambda face: face.bbox[0])
	if order == 'right-left':
		return sorted(faces, key = lambda face: face.bbox[0], reverse = True)
	if order == 'top-bottom':
		return sorted(faces, key = lambda face: face.bbox[1])
	if order == 'bottom-top':
		return sorted(faces, key = lambda face: face.bbox[1], reverse = True)
	if order == 'small-large':
		return sorted(faces, key = lambda face: (face.bbox[2] - face.bbox[0]) * (face.bbox[3] - face.bbox[1]))
	if order == 'large-small':
		return sorted(faces, key = lambda face: (face.bbox[2] - face.bbox[0]) * (face.bbox[3] - face.bbox[1]), reverse = True)
	if order == 'best-worst':
		return sorted(faces, key = lambda face: face.score, reverse = True)
	if order == 'worst-best':
		return sorted(faces, key = lambda face: face.score)
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
		if face.gender == 0 and gender == 'female':
			filter_faces.append(face)
		if face.gender == 1 and gender == 'male':
			filter_faces.append(face)
	return filter_faces
