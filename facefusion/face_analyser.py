from typing import Any, Optional, List, Tuple
import threading
import cv2
import numpy
import onnxruntime

import facefusion.globals
from facefusion.common_helper import get_first
from facefusion.face_helper import warp_face_by_face_landmark_5, warp_face_by_translation, create_static_anchors, distance_to_face_landmark5, distance_to_bbox, apply_nms, categorize_age, categorize_gender
from facefusion.face_store import get_static_faces, set_static_faces
from facefusion.execution_helper import apply_execution_provider_options
from facefusion.download import conditional_download
from facefusion.filesystem import resolve_relative_path
from facefusion.typing import VisionFrame, Face, FaceSet, FaceAnalyserOrder, FaceAnalyserAge, FaceAnalyserGender, ModelSet, Bbox, FaceLandmarkSet, FaceLandmark5, FaceLandmark68, Score, Embedding
from facefusion.vision import resize_frame_resolution, unpack_resolution

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
	'face_detector_yoloface':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/yoloface_8n.onnx',
		'path': resolve_relative_path('../.assets/models/yoloface_8n.onnx')
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
	'face_recognizer_arcface_uniface':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/arcface_w600k_r50.onnx',
		'path': resolve_relative_path('../.assets/models/arcface_w600k_r50.onnx')
	},
	'face_landmarker':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/2dfan4.onnx',
		'path': resolve_relative_path('../.assets/models/2dfan4.onnx')
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
				face_detector = onnxruntime.InferenceSession(MODELS.get('face_detector_retinaface').get('path'), providers = apply_execution_provider_options(facefusion.globals.execution_providers))
			if facefusion.globals.face_detector_model == 'yoloface':
				face_detector = onnxruntime.InferenceSession(MODELS.get('face_detector_yoloface').get('path'), providers = apply_execution_provider_options(facefusion.globals.execution_providers))
			if facefusion.globals.face_detector_model == 'yunet':
				face_detector = cv2.FaceDetectorYN.create(MODELS.get('face_detector_yunet').get('path'), '', (0, 0))
			if facefusion.globals.face_recognizer_model == 'arcface_blendswap':
				face_recognizer = onnxruntime.InferenceSession(MODELS.get('face_recognizer_arcface_blendswap').get('path'), providers = apply_execution_provider_options(facefusion.globals.execution_providers))
			if facefusion.globals.face_recognizer_model == 'arcface_inswapper':
				face_recognizer = onnxruntime.InferenceSession(MODELS.get('face_recognizer_arcface_inswapper').get('path'), providers = apply_execution_provider_options(facefusion.globals.execution_providers))
			if facefusion.globals.face_recognizer_model == 'arcface_simswap':
				face_recognizer = onnxruntime.InferenceSession(MODELS.get('face_recognizer_arcface_simswap').get('path'), providers = apply_execution_provider_options(facefusion.globals.execution_providers))
			if facefusion.globals.face_recognizer_model == 'arcface_uniface':
				face_recognizer = onnxruntime.InferenceSession(MODELS.get('face_recognizer_arcface_uniface').get('path'), providers = apply_execution_provider_options(facefusion.globals.execution_providers))
			face_landmarker = onnxruntime.InferenceSession(MODELS.get('face_landmarker').get('path'), providers = apply_execution_provider_options(facefusion.globals.execution_providers))
			gender_age = onnxruntime.InferenceSession(MODELS.get('gender_age').get('path'), providers = apply_execution_provider_options(facefusion.globals.execution_providers))
			FACE_ANALYSER =\
			{
				'face_detector': face_detector,
				'face_recognizer': face_recognizer,
				'face_landmarker': face_landmarker,
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
			MODELS.get('face_detector_yoloface').get('url'),
			MODELS.get('face_detector_yunet').get('url'),
			MODELS.get('face_recognizer_arcface_blendswap').get('url'),
			MODELS.get('face_recognizer_arcface_inswapper').get('url'),
			MODELS.get('face_recognizer_arcface_simswap').get('url'),
			MODELS.get('face_recognizer_arcface_uniface').get('url'),
			MODELS.get('face_landmarker').get('url'),
			MODELS.get('gender_age').get('url'),
		]
		conditional_download(download_directory_path, model_urls)
	return True


def detect_with_retinaface(frame : VisionFrame, face_detector_size : str) -> Tuple[List[Bbox], List[FaceLandmark5], List[Score]]:
	face_detector = get_face_analyser().get('face_detector')
	face_detector_width, face_detector_height = unpack_resolution(face_detector_size)
	temp_frame = resize_frame_resolution(frame, face_detector_width, face_detector_height)
	frame_height, frame_width, _ = frame.shape
	temp_frame_height, temp_frame_width, _ = temp_frame.shape
	ratio_height = frame_height / temp_frame_height
	ratio_width = frame_width / temp_frame_width
	bbox_list = []
	face_landmark5_list = []
	score_list = []
	feature_strides = [ 8, 16, 32 ]
	feature_map_channel = 3
	anchor_total = 2

	with THREAD_SEMAPHORE:
		detections = face_detector.run(None,
		{
			face_detector.get_inputs()[0].name: prepare_detect_frame(temp_frame, face_detector_size)
		})
	for index, feature_stride in enumerate(feature_strides):
		keep_indices = numpy.where(detections[index] >= facefusion.globals.face_detector_score)[0]
		if keep_indices.any():
			stride_height = face_detector_height // feature_stride
			stride_width = face_detector_width // feature_stride
			anchors = create_static_anchors(feature_stride, anchor_total, stride_height, stride_width)
			bbox_raw = detections[index + feature_map_channel] * feature_stride
			face_landmark_5_raw = detections[index + feature_map_channel * 2] * feature_stride
			for bbox in distance_to_bbox(anchors, bbox_raw)[keep_indices]:
				bbox_list.append(numpy.array(
				[
					bbox[0] * ratio_width,
					bbox[1] * ratio_height,
					bbox[2] * ratio_width,
					bbox[3] * ratio_height
				]))
			for face_landmark5 in distance_to_face_landmark5(anchors, face_landmark_5_raw)[keep_indices]:
				face_landmark5_list.append(face_landmark5 * [ ratio_width, ratio_height ])
			for score in detections[index][keep_indices]:
				score_list.append(score[0])
	return bbox_list, face_landmark5_list, score_list


def detect_with_yoloface(frame : VisionFrame, face_detector_size : str) -> Tuple[List[Bbox], List[FaceLandmark5], List[Score]]:
	face_detector = get_face_analyser().get('face_detector')
	face_detector_width, face_detector_height = unpack_resolution(face_detector_size)
	temp_frame = resize_frame_resolution(frame, face_detector_width, face_detector_height)
	frame_height, frame_width, _ = frame.shape
	temp_frame_height, temp_frame_width, _ = temp_frame.shape
	ratio_height = frame_height / temp_frame_height
	ratio_width = frame_width / temp_frame_width
	bbox_list = []
	face_landmark5_list = []
	score_list = []

	with THREAD_SEMAPHORE:
		detections = face_detector.run(None,
		{
			face_detector.get_inputs()[0].name: prepare_detect_frame(temp_frame, face_detector_size)
		})
	detections = numpy.squeeze(detections).T
	bbox_raw, score_raw, face_landmark_5_raw = numpy.split(detections, [ 4, 5 ], axis = 1)
	keep_indices = numpy.where(score_raw > facefusion.globals.face_detector_score)[0]
	if keep_indices.any():
		bbox_raw, face_landmark_5_raw, score_raw = bbox_raw[keep_indices], face_landmark_5_raw[keep_indices], score_raw[keep_indices]
		for bbox in bbox_raw:
			bbox_list.append(numpy.array(
			[
				(bbox[0] - bbox[2] / 2) * ratio_width,
				(bbox[1] - bbox[3] / 2) * ratio_height,
				(bbox[0] + bbox[2] / 2) * ratio_width,
				(bbox[1] + bbox[3] / 2) * ratio_height
			]))
		face_landmark_5_raw[:, 0::3] = (face_landmark_5_raw[:, 0::3]) * ratio_width
		face_landmark_5_raw[:, 1::3] = (face_landmark_5_raw[:, 1::3]) * ratio_height
		for face_landmark_5 in face_landmark_5_raw:
			indices = numpy.arange(0, len(face_landmark_5), 3)
			face_landmark_5_temp = []
			for index in indices:
				face_landmark_5_temp.append([ face_landmark_5[index], face_landmark_5[index + 1] ])
			face_landmark5_list.append(numpy.array(face_landmark_5_temp))
		score_list = score_raw.ravel().tolist()
	return bbox_list, face_landmark5_list, score_list


def detect_with_yunet(frame : VisionFrame, face_detector_size : str) -> Tuple[List[Bbox], List[FaceLandmark5], List[Score]]:
	face_detector = get_face_analyser().get('face_detector')
	face_detector_width, face_detector_height = unpack_resolution(face_detector_size)
	temp_frame = resize_frame_resolution(frame, face_detector_width, face_detector_height)
	frame_height, frame_width, _ = frame.shape
	temp_frame_height, temp_frame_width, _ = temp_frame.shape
	ratio_height = frame_height / temp_frame_height
	ratio_width = frame_width / temp_frame_width
	bbox_list = []
	face_landmark5_list = []
	score_list = []

	face_detector.setInputSize((temp_frame_width, temp_frame_height))
	face_detector.setScoreThreshold(facefusion.globals.face_detector_score)
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
			face_landmark5_list.append(detection[4:14].reshape((5, 2)) * [ ratio_width, ratio_height ])
			score_list.append(detection[14])
	return bbox_list, face_landmark5_list, score_list


def prepare_detect_frame(frame : VisionFrame, face_detector_size : str) -> VisionFrame:
	face_detector_width, face_detector_height = unpack_resolution(face_detector_size)
	frame_height, frame_width, _ = frame.shape
	detect_frame = numpy.zeros((face_detector_height, face_detector_width, 3))
	detect_frame[:frame_height, :frame_width, :] = frame
	detect_frame = (detect_frame - 127.5) / 128.0
	detect_frame = numpy.expand_dims(detect_frame.transpose(2, 0, 1), axis = 0).astype(numpy.float32)
	return detect_frame


def create_faces(frame : VisionFrame, bbox_list : List[Bbox], face_landmark5_list : List[FaceLandmark5], score_list : List[Score]) -> List[Face]:
	faces = []
	if facefusion.globals.face_detector_score > 0:
		sort_indices = numpy.argsort(-numpy.array(score_list))
		bbox_list = [ bbox_list[index] for index in sort_indices ]
		face_landmark5_list = [ face_landmark5_list[index] for index in sort_indices ]
		score_list = [ score_list[index] for index in sort_indices ]
		keep_indices = apply_nms(bbox_list, 0.4)
		for index in keep_indices:
			bbox = bbox_list[index]
			face_landmark_68 = detect_face_landmark_68(frame, bbox)
			landmark : FaceLandmarkSet =\
			{
				'5': face_landmark5_list[index],
				'5/68': convert_face_landmark_68_to_5(face_landmark_68),
				'68': face_landmark_68
			}
			score = score_list[index]
			embedding, normed_embedding = calc_embedding(frame, landmark['5/68'])
			gender, age = detect_gender_age(frame, bbox)
			faces.append(Face(
				bbox = bbox,
				landmark = landmark,
				score = score,
				embedding = embedding,
				normed_embedding = normed_embedding,
				gender = gender,
				age = age
			))
	return faces


def calc_embedding(temp_frame : VisionFrame, face_landmark_5 : FaceLandmark5) -> Tuple[Embedding, Embedding]:
	face_recognizer = get_face_analyser().get('face_recognizer')
	crop_frame, matrix = warp_face_by_face_landmark_5(temp_frame, face_landmark_5, 'arcface_112_v2', (112, 112))
	crop_frame = crop_frame / 127.5 - 1
	crop_frame = crop_frame[:, :, ::-1].transpose(2, 0, 1).astype(numpy.float32)
	crop_frame = numpy.expand_dims(crop_frame, axis = 0)
	embedding = face_recognizer.run(None,
	{
		face_recognizer.get_inputs()[0].name: crop_frame
	})[0]
	embedding = embedding.ravel()
	normed_embedding = embedding / numpy.linalg.norm(embedding)
	return embedding, normed_embedding


def detect_face_landmark_68(frame : VisionFrame, bbox : Bbox) -> FaceLandmark68:
	face_landmarker = get_face_analyser().get('face_landmarker')
	scale = 195 / numpy.subtract(bbox[2:], bbox[:2]).max()
	translation = (256 - numpy.add(bbox[2:], bbox[:2]) * scale) * 0.5
	crop_frame, affine_matrix = warp_face_by_translation(frame, translation, scale, (256, 256))
	crop_frame = crop_frame.transpose(2, 0, 1).astype(numpy.float32) / 255.0
	face_landmark_68 = face_landmarker.run(None,
	{
		face_landmarker.get_inputs()[0].name: [crop_frame]
	})[0]
	face_landmark_68 = face_landmark_68[:, :, :2][0] / 64
	face_landmark_68 = face_landmark_68.reshape(1, -1, 2) * 256
	face_landmark_68 = cv2.transform(face_landmark_68, cv2.invertAffineTransform(affine_matrix))
	face_landmark_68 = face_landmark_68.reshape(-1, 2)
	return face_landmark_68


def convert_face_landmark_68_to_5(landmark_68 : FaceLandmark68) -> FaceLandmark5:
	left_eye = numpy.mean(landmark_68[36:42], axis = 0)
	right_eye = numpy.mean(landmark_68[42:48], axis = 0)
	nose = landmark_68[30]
	left_mouth_end = landmark_68[48]
	right_mouth_end = landmark_68[54]
	face_landmark_5 = numpy.array([ left_eye, right_eye, nose, left_mouth_end, right_mouth_end ])
	return face_landmark_5


def detect_gender_age(frame : VisionFrame, bbox : Bbox) -> Tuple[int, int]:
	gender_age = get_face_analyser().get('gender_age')
	bbox = bbox.reshape(2, -1)
	scale = 64 / numpy.subtract(*bbox[::-1]).max()
	translation = 48 - bbox.sum(axis = 0) * scale * 0.5
	crop_frame, affine_matrix = warp_face_by_translation(frame, translation, scale, (96, 96))
	crop_frame = crop_frame[:, :, ::-1].transpose(2, 0, 1).astype(numpy.float32)
	crop_frame = numpy.expand_dims(crop_frame, axis = 0)
	prediction = gender_age.run(None,
	{
		gender_age.get_inputs()[0].name: crop_frame
	})[0][0]
	gender = int(numpy.argmax(prediction[:2]))
	age = int(numpy.round(prediction[2] * 100))
	return gender, age


def get_one_face(frame : VisionFrame, position : int = 0) -> Optional[Face]:
	many_faces = get_many_faces(frame)
	if many_faces:
		try:
			return many_faces[position]
		except IndexError:
			return many_faces[-1]
	return None


def get_average_face(frames : List[VisionFrame], position : int = 0) -> Optional[Face]:
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
		first_face = get_first(faces)
		average_face = Face(
			bbox = first_face.bbox,
			landmark = first_face.landmark,
			score = first_face.score,
			embedding = numpy.mean(embedding_list, axis = 0),
			normed_embedding = numpy.mean(normed_embedding_list, axis = 0),
			gender = first_face.gender,
			age = first_face.age
		)
	return average_face


def get_many_faces(frame : VisionFrame) -> List[Face]:
	faces = []
	try:
		faces_cache = get_static_faces(frame)
		if faces_cache:
			faces = faces_cache
		else:
			if facefusion.globals.face_detector_model == 'retinaface':
				bbox_list, face_landmark5_list, score_list = detect_with_retinaface(frame, facefusion.globals.face_detector_size)
				faces = create_faces(frame, bbox_list, face_landmark5_list, score_list)
			if facefusion.globals.face_detector_model == 'yoloface':
				bbox_list, face_landmark5_list, score_list = detect_with_yoloface(frame, facefusion.globals.face_detector_size)
				faces = create_faces(frame, bbox_list, face_landmark5_list, score_list)
			if facefusion.globals.face_detector_model == 'yunet':
				bbox_list, face_landmark5_list, score_list = detect_with_yunet(frame, facefusion.globals.face_detector_size)
				faces = create_faces(frame, bbox_list, face_landmark5_list, score_list)
			if faces:
				set_static_faces(frame, faces)
		if facefusion.globals.face_analyser_order:
			faces = sort_by_order(faces, facefusion.globals.face_analyser_order)
		if facefusion.globals.face_analyser_age:
			faces = filter_by_age(faces, facefusion.globals.face_analyser_age)
		if facefusion.globals.face_analyser_gender:
			faces = filter_by_gender(faces, facefusion.globals.face_analyser_gender)
	except (AttributeError, ValueError):
		pass
	return faces


def find_similar_faces(reference_faces : FaceSet, frame : VisionFrame, face_distance : float) -> List[Face]:
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
	current_face_distance = calc_face_distance(face, reference_face)
	return current_face_distance < face_distance


def calc_face_distance(face : Face, reference_face : Face) -> float:
	if hasattr(face, 'normed_embedding') and hasattr(reference_face, 'normed_embedding'):
		return 1 - numpy.dot(face.normed_embedding, reference_face.normed_embedding)
	return 0


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
		if categorize_age(face.age) == age:
			filter_faces.append(face)
	return filter_faces


def filter_by_gender(faces : List[Face], gender : FaceAnalyserGender) -> List[Face]:
	filter_faces = []
	for face in faces:
		if categorize_gender(face.gender) == gender:
			filter_faces.append(face)
	return filter_faces
