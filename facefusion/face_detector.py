from functools import lru_cache
from typing import List, Sequence, Tuple

import cv2
import numpy

from facefusion import inference_manager, state_manager
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.face_helper import create_rotated_matrix_and_size, create_static_anchors, distance_to_bounding_box, distance_to_face_landmark_5, normalize_bounding_box, transform_bounding_box, transform_points
from facefusion.filesystem import resolve_relative_path
from facefusion.thread_helper import thread_semaphore
from facefusion.types import Angle, BoundingBox, Detection, DownloadScope, DownloadSet, FaceLandmark5, InferencePool, ModelSet, Score, VisionFrame
from facefusion.vision import restrict_frame, unpack_resolution


@lru_cache(maxsize = None)
def create_static_model_set(download_scope : DownloadScope) -> ModelSet:
	return\
	{
		'retinaface':
		{
			'hashes':
			{
				'retinaface':
				{
					'url': resolve_download_url('models-3.0.0', 'retinaface_10g.hash'),
					'path': resolve_relative_path('../.assets/models/retinaface_10g.hash')
				}
			},
			'sources':
			{
				'retinaface':
				{
					'url': resolve_download_url('models-3.0.0', 'retinaface_10g.onnx'),
					'path': resolve_relative_path('../.assets/models/retinaface_10g.onnx')
				}
			}
		},
		'scrfd':
		{
			'hashes':
			{
				'scrfd':
				{
					'url': resolve_download_url('models-3.0.0', 'scrfd_2.5g.hash'),
					'path': resolve_relative_path('../.assets/models/scrfd_2.5g.hash')
				}
			},
			'sources':
			{
				'scrfd':
				{
					'url': resolve_download_url('models-3.0.0', 'scrfd_2.5g.onnx'),
					'path': resolve_relative_path('../.assets/models/scrfd_2.5g.onnx')
				}
			}
		},
		'yolo_face':
		{
			'hashes':
			{
				'yolo_face':
				{
					'url': resolve_download_url('models-3.0.0', 'yoloface_8n.hash'),
					'path': resolve_relative_path('../.assets/models/yoloface_8n.hash')
				}
			},
			'sources':
			{
				'yolo_face':
				{
					'url': resolve_download_url('models-3.0.0', 'yoloface_8n.onnx'),
					'path': resolve_relative_path('../.assets/models/yoloface_8n.onnx')
				}
			}
		}
	}


def get_inference_pool() -> InferencePool:
	model_names = [ state_manager.get_item('face_detector_model') ]
	_, model_source_set = collect_model_downloads()

	return inference_manager.get_inference_pool(__name__, model_names, model_source_set)


def clear_inference_pool() -> None:
	model_names = [ state_manager.get_item('face_detector_model') ]
	inference_manager.clear_inference_pool(__name__, model_names)


def collect_model_downloads() -> Tuple[DownloadSet, DownloadSet]:
	model_set = create_static_model_set('full')
	model_hash_set = {}
	model_source_set = {}

	for face_detector_model in [ 'retinaface', 'scrfd', 'yolo_face' ]:
		if state_manager.get_item('face_detector_model') in [ 'many', face_detector_model ]:
			model_hash_set[face_detector_model] = model_set.get(face_detector_model).get('hashes').get(face_detector_model)
			model_source_set[face_detector_model] = model_set.get(face_detector_model).get('sources').get(face_detector_model)

	return model_hash_set, model_source_set


def pre_check() -> bool:
	model_hash_set, model_source_set = collect_model_downloads()

	return conditional_download_hashes(model_hash_set) and conditional_download_sources(model_source_set)


def detect_faces(vision_frame : VisionFrame) -> Tuple[List[BoundingBox], List[Score], List[FaceLandmark5]]:
	all_bounding_boxes : List[BoundingBox] = []
	all_face_scores : List[Score] = []
	all_face_landmarks_5 : List[FaceLandmark5] = []

	if state_manager.get_item('face_detector_model') in [ 'many', 'retinaface' ]:
		bounding_boxes, face_scores, face_landmarks_5 = detect_with_retinaface(vision_frame, state_manager.get_item('face_detector_size'))
		all_bounding_boxes.extend(bounding_boxes)
		all_face_scores.extend(face_scores)
		all_face_landmarks_5.extend(face_landmarks_5)

	if state_manager.get_item('face_detector_model') in [ 'many', 'scrfd' ]:
		bounding_boxes, face_scores, face_landmarks_5 = detect_with_scrfd(vision_frame, state_manager.get_item('face_detector_size'))
		all_bounding_boxes.extend(bounding_boxes)
		all_face_scores.extend(face_scores)
		all_face_landmarks_5.extend(face_landmarks_5)

	if state_manager.get_item('face_detector_model') in [ 'many', 'yolo_face' ]:
		bounding_boxes, face_scores, face_landmarks_5 = detect_with_yolo_face(vision_frame, state_manager.get_item('face_detector_size'))
		all_bounding_boxes.extend(bounding_boxes)
		all_face_scores.extend(face_scores)
		all_face_landmarks_5.extend(face_landmarks_5)

	all_bounding_boxes = [ normalize_bounding_box(all_bounding_box) for all_bounding_box in all_bounding_boxes ]
	return all_bounding_boxes, all_face_scores, all_face_landmarks_5


def detect_rotated_faces(vision_frame : VisionFrame, angle : Angle) -> Tuple[List[BoundingBox], List[Score], List[FaceLandmark5]]:
	rotated_matrix, rotated_size = create_rotated_matrix_and_size(angle, vision_frame.shape[:2][::-1])
	rotated_vision_frame = cv2.warpAffine(vision_frame, rotated_matrix, rotated_size)
	rotated_inverse_matrix = cv2.invertAffineTransform(rotated_matrix)
	bounding_boxes, face_scores, face_landmarks_5 = detect_faces(rotated_vision_frame)
	bounding_boxes = [ transform_bounding_box(bounding_box, rotated_inverse_matrix) for bounding_box in bounding_boxes ]
	face_landmarks_5 = [ transform_points(face_landmark_5, rotated_inverse_matrix) for face_landmark_5 in face_landmarks_5 ]
	return bounding_boxes, face_scores, face_landmarks_5


def detect_with_retinaface(vision_frame : VisionFrame, face_detector_size : str) -> Tuple[List[BoundingBox], List[Score], List[FaceLandmark5]]:
	bounding_boxes = []
	face_scores = []
	face_landmarks_5 = []
	feature_strides = [ 8, 16, 32 ]
	feature_map_channel = 3
	anchor_total = 2
	face_detector_score = state_manager.get_item('face_detector_score')
	face_detector_width, face_detector_height = unpack_resolution(face_detector_size)
	temp_vision_frame = restrict_frame(vision_frame, (face_detector_width, face_detector_height))
	ratio_height = vision_frame.shape[0] / temp_vision_frame.shape[0]
	ratio_width = vision_frame.shape[1] / temp_vision_frame.shape[1]
	detect_vision_frame = prepare_detect_frame(temp_vision_frame, face_detector_size)
	detect_vision_frame = normalize_detect_frame(detect_vision_frame, [ -1, 1 ])
	detection = forward_with_retinaface(detect_vision_frame)

	for index, feature_stride in enumerate(feature_strides):
		keep_indices = numpy.where(detection[index] >= face_detector_score)[0]

		if numpy.any(keep_indices):
			stride_height = face_detector_height // feature_stride
			stride_width = face_detector_width // feature_stride
			anchors = create_static_anchors(feature_stride, anchor_total, stride_height, stride_width)
			bounding_boxes_raw = detection[index + feature_map_channel] * feature_stride
			face_landmarks_5_raw = detection[index + feature_map_channel * 2] * feature_stride

			for bounding_box_raw in distance_to_bounding_box(anchors, bounding_boxes_raw)[keep_indices]:
				bounding_boxes.append(numpy.array(
				[
					bounding_box_raw[0] * ratio_width,
					bounding_box_raw[1] * ratio_height,
					bounding_box_raw[2] * ratio_width,
					bounding_box_raw[3] * ratio_height
				]))

			for face_score_raw in detection[index][keep_indices]:
				face_scores.append(face_score_raw[0])

			for face_landmark_raw_5 in distance_to_face_landmark_5(anchors, face_landmarks_5_raw)[keep_indices]:
				face_landmarks_5.append(face_landmark_raw_5 * [ ratio_width, ratio_height ])

	return bounding_boxes, face_scores, face_landmarks_5


def detect_with_scrfd(vision_frame : VisionFrame, face_detector_size : str) -> Tuple[List[BoundingBox], List[Score], List[FaceLandmark5]]:
	bounding_boxes = []
	face_scores = []
	face_landmarks_5 = []
	feature_strides = [ 8, 16, 32 ]
	feature_map_channel = 3
	anchor_total = 2
	face_detector_score = state_manager.get_item('face_detector_score')
	face_detector_width, face_detector_height = unpack_resolution(face_detector_size)
	temp_vision_frame = restrict_frame(vision_frame, (face_detector_width, face_detector_height))
	ratio_height = vision_frame.shape[0] / temp_vision_frame.shape[0]
	ratio_width = vision_frame.shape[1] / temp_vision_frame.shape[1]
	detect_vision_frame = prepare_detect_frame(temp_vision_frame, face_detector_size)
	detect_vision_frame = normalize_detect_frame(detect_vision_frame, [ -1, 1 ])
	detection = forward_with_scrfd(detect_vision_frame)

	for index, feature_stride in enumerate(feature_strides):
		keep_indices = numpy.where(detection[index] >= face_detector_score)[0]

		if numpy.any(keep_indices):
			stride_height = face_detector_height // feature_stride
			stride_width = face_detector_width // feature_stride
			anchors = create_static_anchors(feature_stride, anchor_total, stride_height, stride_width)
			bounding_boxes_raw = detection[index + feature_map_channel] * feature_stride
			face_landmarks_5_raw = detection[index + feature_map_channel * 2] * feature_stride

			for bounding_box_raw in distance_to_bounding_box(anchors, bounding_boxes_raw)[keep_indices]:
				bounding_boxes.append(numpy.array(
				[
					bounding_box_raw[0] * ratio_width,
					bounding_box_raw[1] * ratio_height,
					bounding_box_raw[2] * ratio_width,
					bounding_box_raw[3] * ratio_height
				]))

			for face_score_raw in detection[index][keep_indices]:
				face_scores.append(face_score_raw[0])

			for face_landmark_raw_5 in distance_to_face_landmark_5(anchors, face_landmarks_5_raw)[keep_indices]:
				face_landmarks_5.append(face_landmark_raw_5 * [ ratio_width, ratio_height ])

	return bounding_boxes, face_scores, face_landmarks_5


def detect_with_yolo_face(vision_frame : VisionFrame, face_detector_size : str) -> Tuple[List[BoundingBox], List[Score], List[FaceLandmark5]]:
	bounding_boxes = []
	face_scores = []
	face_landmarks_5 = []
	face_detector_score = state_manager.get_item('face_detector_score')
	face_detector_width, face_detector_height = unpack_resolution(face_detector_size)
	temp_vision_frame = restrict_frame(vision_frame, (face_detector_width, face_detector_height))
	ratio_height = vision_frame.shape[0] / temp_vision_frame.shape[0]
	ratio_width = vision_frame.shape[1] / temp_vision_frame.shape[1]
	detect_vision_frame = prepare_detect_frame(temp_vision_frame, face_detector_size)
	detect_vision_frame = normalize_detect_frame(detect_vision_frame, [ 0, 1 ])
	detection = forward_with_yolo_face(detect_vision_frame)
	detection = numpy.squeeze(detection).T
	bounding_boxes_raw, face_scores_raw, face_landmarks_5_raw = numpy.split(detection, [ 4, 5 ], axis = 1)
	keep_indices = numpy.where(face_scores_raw > face_detector_score)[0]

	if numpy.any(keep_indices):
		bounding_boxes_raw, face_scores_raw, face_landmarks_5_raw = bounding_boxes_raw[keep_indices], face_scores_raw[keep_indices], face_landmarks_5_raw[keep_indices]

		for bounding_box_raw in bounding_boxes_raw:
			bounding_boxes.append(numpy.array(
			[
				(bounding_box_raw[0] - bounding_box_raw[2] / 2) * ratio_width,
				(bounding_box_raw[1] - bounding_box_raw[3] / 2) * ratio_height,
				(bounding_box_raw[0] + bounding_box_raw[2] / 2) * ratio_width,
				(bounding_box_raw[1] + bounding_box_raw[3] / 2) * ratio_height
			]))

		face_scores = face_scores_raw.ravel().tolist()
		face_landmarks_5_raw[:, 0::3] = (face_landmarks_5_raw[:, 0::3]) * ratio_width
		face_landmarks_5_raw[:, 1::3] = (face_landmarks_5_raw[:, 1::3]) * ratio_height

		for face_landmark_raw_5 in face_landmarks_5_raw:
			face_landmarks_5.append(numpy.array(face_landmark_raw_5.reshape(-1, 3)[:, :2]))

	return bounding_boxes, face_scores, face_landmarks_5


def forward_with_retinaface(detect_vision_frame : VisionFrame) -> Detection:
	face_detector = get_inference_pool().get('retinaface')

	with thread_semaphore():
		detection = face_detector.run(None,
		{
			'input': detect_vision_frame
		})

	return detection


def forward_with_scrfd(detect_vision_frame : VisionFrame) -> Detection:
	face_detector = get_inference_pool().get('scrfd')

	with thread_semaphore():
		detection = face_detector.run(None,
		{
			'input': detect_vision_frame
		})

	return detection


def forward_with_yolo_face(detect_vision_frame : VisionFrame) -> Detection:
	face_detector = get_inference_pool().get('yolo_face')

	with thread_semaphore():
		detection = face_detector.run(None,
		{
			'input': detect_vision_frame
		})

	return detection


def prepare_detect_frame(temp_vision_frame : VisionFrame, face_detector_size : str) -> VisionFrame:
	face_detector_width, face_detector_height = unpack_resolution(face_detector_size)
	detect_vision_frame = numpy.zeros((face_detector_height, face_detector_width, 3))
	detect_vision_frame[:temp_vision_frame.shape[0], :temp_vision_frame.shape[1], :] = temp_vision_frame
	detect_vision_frame = numpy.expand_dims(detect_vision_frame.transpose(2, 0, 1), axis = 0).astype(numpy.float32)
	return detect_vision_frame


def normalize_detect_frame(detect_vision_frame : VisionFrame, normalize_range : Sequence[int]) -> VisionFrame:
	if normalize_range == [ -1, 1 ]:
		return (detect_vision_frame - 127.5) / 128.0
	if normalize_range == [ 0, 1 ]:
		return detect_vision_frame / 255.0
	return detect_vision_frame
