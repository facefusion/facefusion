from time import sleep
from typing import List, Optional, Tuple

import cv2
import numpy

from facefusion import process_manager, state_manager
from facefusion.common_helper import get_first
from facefusion.download import conditional_download_hashes, conditional_download_sources
from facefusion.execution import create_inference_pool
from facefusion.face_helper import apply_nms, convert_to_face_landmark_5, create_rotated_matrix_and_size, create_static_anchors, distance_to_bounding_box, distance_to_face_landmark_5, estimate_face_angle_from_face_landmark_68, estimate_matrix_by_face_landmark_5, get_nms_threshold, normalize_bounding_box, transform_bounding_box, transform_points, warp_face_by_face_landmark_5, warp_face_by_translation
from facefusion.face_store import get_static_faces, set_static_faces
from facefusion.filesystem import resolve_relative_path
from facefusion.thread_helper import conditional_thread_semaphore, thread_lock, thread_semaphore
from facefusion.typing import Angle, BoundingBox, DownloadSet, Embedding, Face, FaceLandmark5, FaceLandmark68, FaceLandmarkSet, FaceScoreSet, InferencePool, ModelSet, Score, VisionFrame
from facefusion.vision import resize_frame_resolution, unpack_resolution

INFERENCE_POOL : Optional[InferencePool] = None
MODEL_SET : ModelSet =\
{
	'retinaface':
	{
		'hashes':
		{
			'face_detector_retinaface':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/retinaface_10g.hash',
				'path': resolve_relative_path('../.assets/models/retinaface_10g.hash')
			}
		},
		'sources':
		{
			'face_detector_retinaface':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/retinaface_10g.onnx',
				'path': resolve_relative_path('../.assets/models/retinaface_10g.onnx')
			}
		}
	},
	'scrfd':
	{
		'hashes':
		{
			'face_detector_scrfd':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/scrfd_2.5g.hash',
				'path': resolve_relative_path('../.assets/models/scrfd_2.5g.hash')
			}
		},
		'sources':
		{
			'face_detector_scrfd':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/scrfd_2.5g.onnx',
				'path': resolve_relative_path('../.assets/models/scrfd_2.5g.onnx')
			}
		}
	},
	'yoloface':
	{
		'hashes':
		{
			'face_detector_yoloface':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/yoloface_8n.hash',
				'path': resolve_relative_path('../.assets/models/yoloface_8n.hash')
			}
		},
		'sources':
		{
			'face_detector_yoloface':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/yoloface_8n.onnx',
				'path': resolve_relative_path('../.assets/models/yoloface_8n.onnx')
			}
		}
	},
	'arcface':
	{
		'hashes':
		{
			'face_recognizer':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/arcface_w600k_r50.hash',
				'path': resolve_relative_path('../.assets/models/arcface_w600k_r50.hash')
			}
		},
		'sources':
		{
			'face_recognizer':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/arcface_w600k_r50.onnx',
				'path': resolve_relative_path('../.assets/models/arcface_w600k_r50.onnx')
			}
		}
	},
	'2dfan4':
	{
		'hashes':
		{
			'face_landmarker_2dfan4':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/2dfan4.hash',
				'path': resolve_relative_path('../.assets/models/2dfan4.hash')
			}
		},
		'sources':
		{
			'face_landmarker_2dfan4':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/2dfan4.onnx',
				'path': resolve_relative_path('../.assets/models/2dfan4.onnx')
			}
		}
	},
	'peppa_wutz':
	{
		'hashes':
		{
			'face_landmarker_peppa_wutz':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/peppa_wutz.hash',
				'path': resolve_relative_path('../.assets/models/peppa_wutz.hash')
			}
		},
		'sources':
		{
			'face_landmarker_peppa_wutz':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/peppa_wutz.onnx',
				'path': resolve_relative_path('../.assets/models/peppa_wutz.onnx')
			}
		}
	},
	'face_landmarker_68_5':
	{
		'hashes':
		{
			'face_landmarker_68_5':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/face_landmarker_68_5.hash',
				'path': resolve_relative_path('../.assets/models/face_landmarker_68_5.hash')
			}
		},
		'sources':
		{
			'face_landmarker_68_5':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/face_landmarker_68_5.onnx',
				'path': resolve_relative_path('../.assets/models/face_landmarker_68_5.onnx')
			}
		}
	},
	'gender_age':
	{
		'hashes':
		{
			'gender_age':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/gender_age.hash',
				'path': resolve_relative_path('../.assets/models/gender_age.hash')
			}
		},
		'sources':
		{
			'gender_age':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/gender_age.onnx',
				'path': resolve_relative_path('../.assets/models/gender_age.onnx')
			}
		}
	}
}


def get_inference_pool() -> InferencePool:
	global INFERENCE_POOL

	with thread_lock():
		while process_manager.is_checking():
			sleep(0.5)
		if INFERENCE_POOL is None:
			model_sources = collect_model_sources()
			INFERENCE_POOL = create_inference_pool(model_sources, state_manager.get_item('execution_device_id'), state_manager.get_item('execution_providers'))
		return INFERENCE_POOL


def clear_inference_pool() -> None:
	global INFERENCE_POOL

	INFERENCE_POOL = None


def collect_model_hashes() -> DownloadSet:
	model_hashes =\
	{
		'face_recognizer': MODEL_SET.get('arcface').get('hashes').get('face_recognizer'),
		'face_landmarker_68_5': MODEL_SET.get('face_landmarker_68_5').get('hashes').get('face_landmarker_68_5'),
		'gender_age': MODEL_SET.get('gender_age').get('hashes').get('gender_age')
	}

	if state_manager.get_item('face_detector_model') in [ 'many', 'retinaface' ]:
		model_hashes['face_detector_retinaface'] = MODEL_SET.get('retinaface').get('hashes').get('face_detector_retinaface')
	if state_manager.get_item('face_detector_model') in [ 'many', 'scrfd' ]:
		model_hashes['face_detector_scrfd'] = MODEL_SET.get('scrfd').get('hashes').get('face_detector_scrfd')
	if state_manager.get_item('face_detector_model') in [ 'many', 'yoloface' ]:
		model_hashes['face_detector_yoloface'] = MODEL_SET.get('yoloface').get('hashes').get('face_detector_yoloface')
	if state_manager.get_item('face_landmarker_model') in [ 'many', '2dfan4' ]:
		model_hashes['face_landmarker_2dfan4'] = MODEL_SET.get('2dfan4').get('hashes').get('face_landmarker_2dfan4')
	if state_manager.get_item('face_landmarker_model') in [ 'many', 'peppa_wutz' ]:
		model_hashes['face_landmarker_peppa_wutz'] = MODEL_SET.get('peppa_wutz').get('hashes').get('face_landmarker_peppa_wutz')
	return model_hashes


def collect_model_sources() -> DownloadSet:
	model_sources =\
	{
		'face_recognizer': MODEL_SET.get('arcface').get('sources').get('face_recognizer'),
		'face_landmarker_68_5': MODEL_SET.get('face_landmarker_68_5').get('sources').get('face_landmarker_68_5'),
		'gender_age': MODEL_SET.get('gender_age').get('sources').get('gender_age')
	}

	if state_manager.get_item('face_detector_model') in [ 'many', 'retinaface' ]:
		model_sources['face_detector_retinaface'] = MODEL_SET.get('retinaface').get('sources').get('face_detector_retinaface')
	if state_manager.get_item('face_detector_model') in [ 'many', 'scrfd' ]:
		model_sources['face_detector_scrfd'] = MODEL_SET.get('scrfd').get('sources').get('face_detector_scrfd')
	if state_manager.get_item('face_detector_model') in [ 'many', 'yoloface' ]:
		model_sources['face_detector_yoloface'] = MODEL_SET.get('yoloface').get('sources').get('face_detector_yoloface')
	if state_manager.get_item('face_landmarker_model') in [ 'many', '2dfan4' ]:
		model_sources['face_landmarker_2dfan4'] = MODEL_SET.get('2dfan4').get('sources').get('face_landmarker_2dfan4')
	if state_manager.get_item('face_landmarker_model') in [ 'many', 'peppa_wutz' ]:
		model_sources['face_landmarker_peppa_wutz'] = MODEL_SET.get('peppa_wutz').get('sources').get('face_landmarker_peppa_wutz')
	return model_sources


def pre_check() -> bool:
	download_directory_path = resolve_relative_path('../.assets/models')
	model_hashes = collect_model_hashes()
	model_sources = collect_model_sources()

	return conditional_download_hashes(download_directory_path, model_hashes) and conditional_download_sources(download_directory_path, model_sources)


def detect_with_retinaface(vision_frame : VisionFrame, face_detector_size : str) -> Tuple[List[BoundingBox], List[FaceLandmark5], List[Score]]:
	face_detector = get_inference_pool().get('face_detector_retinaface')
	face_detector_width, face_detector_height = unpack_resolution(face_detector_size)
	temp_vision_frame = resize_frame_resolution(vision_frame, (face_detector_width, face_detector_height))
	ratio_height = vision_frame.shape[0] / temp_vision_frame.shape[0]
	ratio_width = vision_frame.shape[1] / temp_vision_frame.shape[1]
	feature_strides = [ 8, 16, 32 ]
	feature_map_channel = 3
	anchor_total = 2
	bounding_boxes = []
	face_landmarks_5 = []
	face_scores = []

	detect_vision_frame = prepare_detect_frame(temp_vision_frame, face_detector_size)
	with thread_semaphore():
		detections = face_detector.run(None,
		{
			'input': detect_vision_frame
		})

	for index, feature_stride in enumerate(feature_strides):
		keep_indices = numpy.where(detections[index] >= state_manager.get_item('face_detector_score'))[0]
		if numpy.any(keep_indices):
			stride_height = face_detector_height // feature_stride
			stride_width = face_detector_width // feature_stride
			anchors = create_static_anchors(feature_stride, anchor_total, stride_height, stride_width)
			bounding_box_raw = detections[index + feature_map_channel] * feature_stride
			face_landmark_5_raw = detections[index + feature_map_channel * 2] * feature_stride
			for bounding_box in distance_to_bounding_box(anchors, bounding_box_raw)[keep_indices]:
				bounding_boxes.append(numpy.array(
				[
					bounding_box[0] * ratio_width,
					bounding_box[1] * ratio_height,
					bounding_box[2] * ratio_width,
					bounding_box[3] * ratio_height,
				]))
			for face_landmark_5 in distance_to_face_landmark_5(anchors, face_landmark_5_raw)[keep_indices]:
				face_landmarks_5.append(face_landmark_5 * [ ratio_width, ratio_height ])
			for score in detections[index][keep_indices]:
				face_scores.append(score[0])
	return bounding_boxes, face_landmarks_5, face_scores


def detect_with_scrfd(vision_frame : VisionFrame, face_detector_size : str) -> Tuple[List[BoundingBox], List[FaceLandmark5], List[Score]]:
	face_detector = get_inference_pool().get('face_detector_scrfd')
	face_detector_width, face_detector_height = unpack_resolution(face_detector_size)
	temp_vision_frame = resize_frame_resolution(vision_frame, (face_detector_width, face_detector_height))
	ratio_height = vision_frame.shape[0] / temp_vision_frame.shape[0]
	ratio_width = vision_frame.shape[1] / temp_vision_frame.shape[1]
	feature_strides = [ 8, 16, 32 ]
	feature_map_channel = 3
	anchor_total = 2
	bounding_boxes = []
	face_landmarks_5 = []
	face_scores = []

	detect_vision_frame = prepare_detect_frame(temp_vision_frame, face_detector_size)
	with thread_semaphore():
		detections = face_detector.run(None,
		{
			'input': detect_vision_frame
		})

	for index, feature_stride in enumerate(feature_strides):
		keep_indices = numpy.where(detections[index] >= state_manager.get_item('face_detector_score'))[0]
		if numpy.any(keep_indices):
			stride_height = face_detector_height // feature_stride
			stride_width = face_detector_width // feature_stride
			anchors = create_static_anchors(feature_stride, anchor_total, stride_height, stride_width)
			bounding_box_raw = detections[index + feature_map_channel] * feature_stride
			face_landmark_5_raw = detections[index + feature_map_channel * 2] * feature_stride
			for bounding_box in distance_to_bounding_box(anchors, bounding_box_raw)[keep_indices]:
				bounding_boxes.append(numpy.array(
				[
					bounding_box[0] * ratio_width,
					bounding_box[1] * ratio_height,
					bounding_box[2] * ratio_width,
					bounding_box[3] * ratio_height,
				]))
			for face_landmark_5 in distance_to_face_landmark_5(anchors, face_landmark_5_raw)[keep_indices]:
				face_landmarks_5.append(face_landmark_5 * [ ratio_width, ratio_height ])
			for score in detections[index][keep_indices]:
				face_scores.append(score[0])
	return bounding_boxes, face_landmarks_5, face_scores


def detect_with_yoloface(vision_frame : VisionFrame, face_detector_size : str) -> Tuple[List[BoundingBox], List[FaceLandmark5], List[Score]]:
	face_detector = get_inference_pool().get('face_detector_yoloface')
	face_detector_width, face_detector_height = unpack_resolution(face_detector_size)
	temp_vision_frame = resize_frame_resolution(vision_frame, (face_detector_width, face_detector_height))
	ratio_height = vision_frame.shape[0] / temp_vision_frame.shape[0]
	ratio_width = vision_frame.shape[1] / temp_vision_frame.shape[1]
	bounding_boxes = []
	face_landmarks_5 = []
	face_scores = []

	detect_vision_frame = prepare_detect_frame(temp_vision_frame, face_detector_size)
	with thread_semaphore():
		detections = face_detector.run(None,
		{
			'input': detect_vision_frame
		})

	detections = numpy.squeeze(detections).T
	bounding_box_raw, score_raw, face_landmark_5_raw = numpy.split(detections, [ 4, 5 ], axis = 1)
	keep_indices = numpy.where(score_raw > state_manager.get_item('face_detector_score'))[0]
	if numpy.any(keep_indices):
		bounding_box_raw, face_landmark_5_raw, score_raw = bounding_box_raw[keep_indices], face_landmark_5_raw[keep_indices], score_raw[keep_indices]
		for bounding_box in bounding_box_raw:
			bounding_boxes.append(numpy.array(
			[
				(bounding_box[0] - bounding_box[2] / 2) * ratio_width,
				(bounding_box[1] - bounding_box[3] / 2) * ratio_height,
				(bounding_box[0] + bounding_box[2] / 2) * ratio_width,
				(bounding_box[1] + bounding_box[3] / 2) * ratio_height,
			]))
		face_landmark_5_raw[:, 0::3] = (face_landmark_5_raw[:, 0::3]) * ratio_width
		face_landmark_5_raw[:, 1::3] = (face_landmark_5_raw[:, 1::3]) * ratio_height
		for face_landmark_5 in face_landmark_5_raw:
			face_landmarks_5.append(numpy.array(face_landmark_5.reshape(-1, 3)[:, :2]))
		face_scores = score_raw.ravel().tolist()
	return bounding_boxes, face_landmarks_5, face_scores


def detect_faces(vision_frame : VisionFrame) -> Tuple[List[BoundingBox], List[FaceLandmark5], List[Score]]:
	bounding_boxes = []
	face_landmarks_5 = []
	face_scores = []

	if state_manager.get_item('face_detector_model') in [ 'many', 'retinaface' ]:
		bounding_boxes_retinaface, face_landmarks_5_retinaface, face_scores_retinaface = detect_with_retinaface(vision_frame, state_manager.get_item('face_detector_size'))
		bounding_boxes.extend(bounding_boxes_retinaface)
		face_landmarks_5.extend(face_landmarks_5_retinaface)
		face_scores.extend(face_scores_retinaface)

	if state_manager.get_item('face_detector_model') in [ 'many', 'scrfd' ]:
		bounding_boxes_scrfd, face_landmarks_5_scrfd, face_scores_scrfd = detect_with_scrfd(vision_frame, state_manager.get_item('face_detector_size'))
		bounding_boxes.extend(bounding_boxes_scrfd)
		face_landmarks_5.extend(face_landmarks_5_scrfd)
		face_scores.extend(face_scores_scrfd)

	if state_manager.get_item('face_detector_model') in [ 'many', 'yoloface' ]:
		bounding_boxes_yoloface, face_landmarks_5_yoloface, face_scores_yoloface = detect_with_yoloface(vision_frame, state_manager.get_item('face_detector_size'))
		bounding_boxes.extend(bounding_boxes_yoloface)
		face_landmarks_5.extend(face_landmarks_5_yoloface)
		face_scores.extend(face_scores_yoloface)

	bounding_boxes = [ normalize_bounding_box(bounding_box) for bounding_box in bounding_boxes ]
	return bounding_boxes, face_landmarks_5, face_scores


def detect_rotated_faces(vision_frame : VisionFrame, angle : Angle) -> Tuple[List[BoundingBox], List[FaceLandmark5], List[Score]]:
	rotated_matrix, rotated_size = create_rotated_matrix_and_size(angle, vision_frame.shape[:2][::-1])
	rotated_vision_frame = cv2.warpAffine(vision_frame, rotated_matrix, rotated_size)
	inverse_rotated_matrix = cv2.invertAffineTransform(rotated_matrix)
	bounding_boxes, face_landmarks_5, face_scores = detect_faces(rotated_vision_frame)
	bounding_boxes = [ transform_bounding_box(bounding_box, inverse_rotated_matrix) for bounding_box in bounding_boxes ]
	face_landmarks_5 = [ transform_points(face_landmark_5, inverse_rotated_matrix) for face_landmark_5 in face_landmarks_5 ]
	return bounding_boxes, face_landmarks_5, face_scores


def prepare_detect_frame(temp_vision_frame : VisionFrame, face_detector_size : str) -> VisionFrame:
	face_detector_width, face_detector_height = unpack_resolution(face_detector_size)
	detect_vision_frame = numpy.zeros((face_detector_height, face_detector_width, 3))
	detect_vision_frame[:temp_vision_frame.shape[0], :temp_vision_frame.shape[1], :] = temp_vision_frame
	detect_vision_frame = (detect_vision_frame - 127.5) / 128.0
	detect_vision_frame = numpy.expand_dims(detect_vision_frame.transpose(2, 0, 1), axis = 0).astype(numpy.float32)
	return detect_vision_frame


def create_faces(vision_frame : VisionFrame, bounding_boxes : List[BoundingBox], face_landmarks_5 : List[FaceLandmark5], face_scores : List[Score]) -> List[Face]:
	faces = []
	nms_threshold = get_nms_threshold(state_manager.get_item('face_detector_model'), state_manager.get_item('face_detector_angles'))
	keep_indices = apply_nms(bounding_boxes, face_scores, state_manager.get_item('face_detector_score'), nms_threshold)

	for index in keep_indices:
		bounding_box = bounding_boxes[index]
		face_landmark_5 = face_landmarks_5[index]
		face_landmark_5_68 = face_landmark_5
		face_landmark_68_5 = expand_face_landmark_68_from_5(face_landmark_5_68)
		face_landmark_68 = face_landmark_68_5
		face_landmark_score_68 = 0.0
		face_score = face_scores[index]
		face_angle = estimate_face_angle_from_face_landmark_68(face_landmark_68_5)

		if state_manager.get_item('face_landmarker_score') > 0:
			face_landmark_score_2dfan4 = 0.0
			face_landmark_score_peppa_wutz = 0.0
			if state_manager.get_item('face_landmarker_model') in [ 'many', '2dfan4' ]:
				face_landmark_2dfan4, face_landmark_score_2dfan4 = detect_with_2dfan4(vision_frame, bounding_box, face_angle)
			if state_manager.get_item('face_landmarker_model') in [ 'many', 'peppa_wutz' ]:
				face_landmark_peppa_wutz, face_landmark_score_peppa_wutz = detect_with_peppa_wutz(vision_frame, bounding_box, face_angle)
			if face_landmark_score_2dfan4 > face_landmark_score_peppa_wutz:
				face_landmark_68 = face_landmark_2dfan4
				face_landmark_score_68 = face_landmark_score_2dfan4
			else:
				face_landmark_68 = face_landmark_peppa_wutz
				face_landmark_score_68 = face_landmark_score_peppa_wutz
			if face_landmark_score_68 > state_manager.get_item('face_landmarker_score'):
				face_landmark_5_68 = convert_to_face_landmark_5(face_landmark_68)

		face_landmark_set : FaceLandmarkSet =\
		{
			'5': face_landmark_5,
			'5/68': face_landmark_5_68,
			'68': face_landmark_68,
			'68/5': face_landmark_68_5
		}
		face_score_set : FaceScoreSet =\
		{
			'detector': face_score,
			'landmarker': face_landmark_score_68
		}
		embedding, normed_embedding = calc_embedding(vision_frame, face_landmark_set.get('5/68'))
		gender, age = detect_gender_age(vision_frame, bounding_box)
		faces.append(Face(
			bounding_box = bounding_box,
			landmark_set = face_landmark_set,
			score_set = face_score_set,
			angle = face_angle,
			embedding = embedding,
			normed_embedding = normed_embedding,
			gender = gender,
			age = age
		))
	return faces


def calc_embedding(temp_vision_frame : VisionFrame, face_landmark_5 : FaceLandmark5) -> Tuple[Embedding, Embedding]:
	face_recognizer = get_inference_pool().get('face_recognizer')
	crop_vision_frame, matrix = warp_face_by_face_landmark_5(temp_vision_frame, face_landmark_5, 'arcface_112_v2', (112, 112))
	crop_vision_frame = crop_vision_frame / 127.5 - 1
	crop_vision_frame = crop_vision_frame[:, :, ::-1].transpose(2, 0, 1).astype(numpy.float32)
	crop_vision_frame = numpy.expand_dims(crop_vision_frame, axis = 0)

	with conditional_thread_semaphore():
		embedding = face_recognizer.run(None,
		{
			'input': crop_vision_frame
		})[0]

	embedding = embedding.ravel()
	normed_embedding = embedding / numpy.linalg.norm(embedding)
	return embedding, normed_embedding


def detect_with_2dfan4(temp_vision_frame : VisionFrame, bounding_box : BoundingBox, face_angle : Angle) -> Tuple[FaceLandmark68, Score]:
	face_landmarker = get_inference_pool().get('face_landmarker_2dfan4')
	scale = 195 / numpy.subtract(bounding_box[2:], bounding_box[:2]).max().clip(1, None)
	translation = (256 - numpy.add(bounding_box[2:], bounding_box[:2]) * scale) * 0.5
	rotated_matrix, rotated_size = create_rotated_matrix_and_size(face_angle, (256, 256))
	crop_vision_frame, affine_matrix = warp_face_by_translation(temp_vision_frame, translation, scale, (256, 256))
	crop_vision_frame = cv2.warpAffine(crop_vision_frame, rotated_matrix, rotated_size)
	crop_vision_frame = conditional_optimize_contrast(crop_vision_frame)
	crop_vision_frame = crop_vision_frame.transpose(2, 0, 1).astype(numpy.float32) / 255.0

	with conditional_thread_semaphore():
		face_landmark_68, face_heatmap = face_landmarker.run(None,
		{
			'input': [ crop_vision_frame ]
		})

	face_landmark_68 = face_landmark_68[:, :, :2][0] / 64 * 256
	face_landmark_68 = transform_points(face_landmark_68, cv2.invertAffineTransform(rotated_matrix))
	face_landmark_68 = transform_points(face_landmark_68, cv2.invertAffineTransform(affine_matrix))
	face_landmark_score_68 = numpy.amax(face_heatmap, axis = (2, 3))
	face_landmark_score_68 = numpy.mean(face_landmark_score_68)
	return face_landmark_68, face_landmark_score_68


def detect_with_peppa_wutz(temp_vision_frame : VisionFrame, bounding_box : BoundingBox, face_angle : Angle) -> Tuple[FaceLandmark68, Score]:
	face_landmarker = get_inference_pool().get('face_landmarker_peppa_wutz')
	scale = 195 / numpy.subtract(bounding_box[2:], bounding_box[:2]).max().clip(1, None)
	translation = (256 - numpy.add(bounding_box[2:], bounding_box[:2]) * scale) * 0.5
	rotated_matrix, rotated_size = create_rotated_matrix_and_size(face_angle, (256, 256))
	crop_vision_frame, affine_matrix = warp_face_by_translation(temp_vision_frame, translation, scale, (256, 256))
	crop_vision_frame = cv2.warpAffine(crop_vision_frame, rotated_matrix, rotated_size)
	crop_vision_frame = conditional_optimize_contrast(crop_vision_frame)
	crop_vision_frame = crop_vision_frame.transpose(2, 0, 1).astype(numpy.float32) / 255.0
	crop_vision_frame = numpy.expand_dims(crop_vision_frame, axis = 0)

	with conditional_thread_semaphore():
		prediction = face_landmarker.run(None,
		{
			'input': crop_vision_frame
		})[0]

	face_landmark_68 = prediction.reshape(-1, 3)[:, :2] / 64 * 256
	face_landmark_68 = transform_points(face_landmark_68, cv2.invertAffineTransform(rotated_matrix))
	face_landmark_68 = transform_points(face_landmark_68, cv2.invertAffineTransform(affine_matrix))
	face_landmark_score_68 = prediction.reshape(-1, 3)[:, 2].mean()
	return face_landmark_68, face_landmark_score_68


def conditional_optimize_contrast(crop_vision_frame : VisionFrame) -> VisionFrame:
	crop_vision_frame = cv2.cvtColor(crop_vision_frame, cv2.COLOR_RGB2Lab)
	if numpy.mean(crop_vision_frame[:, :, 0]) < 30:  # type:ignore[arg-type]
		crop_vision_frame[:, :, 0] = cv2.createCLAHE(clipLimit = 2).apply(crop_vision_frame[:, :, 0])
	crop_vision_frame = cv2.cvtColor(crop_vision_frame, cv2.COLOR_Lab2RGB)
	return crop_vision_frame


def expand_face_landmark_68_from_5(face_landmark_5 : FaceLandmark5) -> FaceLandmark68:
	face_landmarker = get_inference_pool().get('face_landmarker_68_5')
	affine_matrix = estimate_matrix_by_face_landmark_5(face_landmark_5, 'ffhq_512', (1, 1))
	face_landmark_5 = cv2.transform(face_landmark_5.reshape(1, -1, 2), affine_matrix).reshape(-1, 2)

	with conditional_thread_semaphore():
		face_landmark_68_5 = face_landmarker.run(None,
		{
			'input': [ face_landmark_5 ]
		})[0][0]

	face_landmark_68_5 = cv2.transform(face_landmark_68_5.reshape(1, -1, 2), cv2.invertAffineTransform(affine_matrix)).reshape(-1, 2)
	return face_landmark_68_5


def detect_gender_age(temp_vision_frame : VisionFrame, bounding_box : BoundingBox) -> Tuple[int, int]:
	gender_age = get_inference_pool().get('gender_age')
	bounding_box = bounding_box.reshape(2, -1)
	scale = 64 / numpy.subtract(*bounding_box[::-1]).max()
	translation = 48 - bounding_box.sum(axis = 0) * scale * 0.5
	crop_vision_frame, affine_matrix = warp_face_by_translation(temp_vision_frame, translation, scale, (96, 96))
	crop_vision_frame = crop_vision_frame[:, :, ::-1].transpose(2, 0, 1).astype(numpy.float32)
	crop_vision_frame = numpy.expand_dims(crop_vision_frame, axis = 0)

	with conditional_thread_semaphore():
		prediction = gender_age.run(None,
		{
			'input': crop_vision_frame
		})[0][0]

	gender = int(numpy.argmax(prediction[:2]))
	age = int(numpy.round(prediction[2] * 100))
	return gender, age


def get_one_face(faces : List[Face], position : int = 0) -> Optional[Face]:
	if faces:
		position = min(position, len(faces) - 1)
		return faces[position]
	return None


def get_average_face(faces : List[Face]) -> Optional[Face]:
	embeddings = []
	normed_embeddings = []

	if faces:
		first_face = get_first(faces)

		for face in faces:
			embeddings.append(face.embedding)
			normed_embeddings.append(face.normed_embedding)

		return Face(
			bounding_box = first_face.bounding_box,
			landmark_set = first_face.landmark_set,
			score_set = first_face.score_set,
			angle = first_face.angle,
			embedding = numpy.mean(embeddings, axis = 0),
			normed_embedding = numpy.mean(normed_embeddings, axis = 0),
			gender = first_face.gender,
			age = first_face.age
		)
	return None


def get_many_faces(vision_frames : List[VisionFrame]) -> List[Face]:
	many_faces : List[Face] = []

	for vision_frame in vision_frames:
		if numpy.any(vision_frame):
			static_faces = get_static_faces(vision_frame)
			if static_faces:
				many_faces.extend(static_faces)
			else:
				all_bounding_boxes = []
				all_face_landmarks_5 = []
				all_face_scores = []

				for face_detector_angle in state_manager.get_item('face_detector_angles'):
					if face_detector_angle == 0:
						bounding_boxes, face_landmarks_5, face_scores = detect_faces(vision_frame)
					else:
						bounding_boxes, face_landmarks_5, face_scores = detect_rotated_faces(vision_frame, face_detector_angle)
					all_bounding_boxes.extend(bounding_boxes)
					all_face_landmarks_5.extend(face_landmarks_5)
					all_face_scores.extend(face_scores)

				if all_bounding_boxes and all_face_landmarks_5 and all_face_scores and state_manager.get_item('face_detector_score') > 0:
					faces = create_faces(vision_frame, all_bounding_boxes, all_face_landmarks_5, all_face_scores)

					if faces:
						many_faces.extend(faces)
						set_static_faces(vision_frame, faces)
	return many_faces
