from typing import List, Tuple

import cv2
import numpy

from facefusion import inference_manager, state_manager
from facefusion.download import conditional_download_hashes, conditional_download_sources
from facefusion.face_helper import create_rotated_matrix_and_size, create_static_anchors, distance_to_bounding_box, distance_to_face_landmark_5, normalize_bounding_box, transform_bounding_box, transform_points
from facefusion.filesystem import resolve_relative_path
from facefusion.thread_helper import thread_semaphore
from facefusion.typing import Angle, BoundingBox, Detection, DownloadSet, FaceLandmark5, InferencePool, ModelSet, Score, VisionFrame
from facefusion.vision import resize_frame_resolution, unpack_resolution

MODEL_SET : ModelSet =\
{
	'retinaface':
	{
		'hashes':
		{
			'retinaface':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/retinaface_10g.hash',
				'path': resolve_relative_path('../.assets/models/retinaface_10g.hash')
			}
		},
		'sources':
		{
			'retinaface':
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
			'scrfd':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/scrfd_2.5g.hash',
				'path': resolve_relative_path('../.assets/models/scrfd_2.5g.hash')
			}
		},
		'sources':
		{
			'scrfd':
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
			'yoloface':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/yoloface_8n.hash',
				'path': resolve_relative_path('../.assets/models/yoloface_8n.hash')
			}
		},
		'sources':
		{
			'yoloface':
			{
				'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models-3.0.0/yoloface_8n.onnx',
				'path': resolve_relative_path('../.assets/models/yoloface_8n.onnx')
			}
		}
	}
}


def get_inference_pool() -> InferencePool:
	_, model_sources = collect_model_downloads()
	model_context = __name__ + '.' + state_manager.get_item('face_detector_model')
	return inference_manager.get_inference_pool(model_context, model_sources)


def clear_inference_pool() -> None:
	model_context = __name__ + '.' + state_manager.get_item('face_detector_model')
	inference_manager.clear_inference_pool(model_context)


def collect_model_downloads() -> Tuple[DownloadSet, DownloadSet]:
	model_hashes = {}
	model_sources = {}

	if state_manager.get_item('face_detector_model') in [ 'many', 'retinaface' ]:
		model_hashes['retinaface'] = MODEL_SET.get('retinaface').get('hashes').get('retinaface')
		model_sources['retinaface'] = MODEL_SET.get('retinaface').get('sources').get('retinaface')
	if state_manager.get_item('face_detector_model') in [ 'many', 'scrfd' ]:
		model_hashes['scrfd'] = MODEL_SET.get('scrfd').get('hashes').get('scrfd')
		model_sources['scrfd'] = MODEL_SET.get('scrfd').get('sources').get('scrfd')
	if state_manager.get_item('face_detector_model') in [ 'many', 'yoloface' ]:
		model_hashes['yoloface'] = MODEL_SET.get('yoloface').get('hashes').get('yoloface')
		model_sources['yoloface'] = MODEL_SET.get('yoloface').get('sources').get('yoloface')
	return model_hashes, model_sources


def pre_check() -> bool:
	download_directory_path = resolve_relative_path('../.assets/models')
	model_hashes, model_sources = collect_model_downloads()

	return conditional_download_hashes(download_directory_path, model_hashes) and conditional_download_sources(download_directory_path, model_sources)


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

	if state_manager.get_item('face_detector_model') in [ 'many', 'yoloface' ]:
		bounding_boxes, face_scores, face_landmarks_5 = detect_with_yoloface(vision_frame, state_manager.get_item('face_detector_size'))
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
	face_detector_width, face_detector_height = unpack_resolution(face_detector_size)
	temp_vision_frame = resize_frame_resolution(vision_frame, (face_detector_width, face_detector_height))
	ratio_height = vision_frame.shape[0] / temp_vision_frame.shape[0]
	ratio_width = vision_frame.shape[1] / temp_vision_frame.shape[1]
	detect_vision_frame = prepare_detect_frame(temp_vision_frame, face_detector_size)
	detection = forward_with_retinaface(detect_vision_frame)

	for index, feature_stride in enumerate(feature_strides):
		keep_indices = numpy.where(detection[index] >= state_manager.get_item('face_detector_score'))[0]

		if numpy.any(keep_indices):
			stride_height = face_detector_height // feature_stride
			stride_width = face_detector_width // feature_stride
			anchors = create_static_anchors(feature_stride, anchor_total, stride_height, stride_width)
			bounding_box_raw = detection[index + feature_map_channel] * feature_stride
			face_landmark_5_raw = detection[index + feature_map_channel * 2] * feature_stride

			for bounding_box in distance_to_bounding_box(anchors, bounding_box_raw)[keep_indices]:
				bounding_boxes.append(numpy.array(
				[
					bounding_box[0] * ratio_width,
					bounding_box[1] * ratio_height,
					bounding_box[2] * ratio_width,
					bounding_box[3] * ratio_height,
				]))

			for score in detection[index][keep_indices]:
				face_scores.append(score[0])

			for face_landmark_5 in distance_to_face_landmark_5(anchors, face_landmark_5_raw)[keep_indices]:
				face_landmarks_5.append(face_landmark_5 * [ ratio_width, ratio_height ])

	return bounding_boxes, face_scores, face_landmarks_5


def detect_with_scrfd(vision_frame : VisionFrame, face_detector_size : str) -> Tuple[List[BoundingBox], List[Score], List[FaceLandmark5]]:
	bounding_boxes = []
	face_scores = []
	face_landmarks_5 = []
	feature_strides = [ 8, 16, 32 ]
	feature_map_channel = 3
	anchor_total = 2
	face_detector_width, face_detector_height = unpack_resolution(face_detector_size)
	temp_vision_frame = resize_frame_resolution(vision_frame, (face_detector_width, face_detector_height))
	ratio_height = vision_frame.shape[0] / temp_vision_frame.shape[0]
	ratio_width = vision_frame.shape[1] / temp_vision_frame.shape[1]
	detect_vision_frame = prepare_detect_frame(temp_vision_frame, face_detector_size)
	detection = forward_with_scrfd(detect_vision_frame)

	for index, feature_stride in enumerate(feature_strides):
		keep_indices = numpy.where(detection[index] >= state_manager.get_item('face_detector_score'))[0]

		if numpy.any(keep_indices):
			stride_height = face_detector_height // feature_stride
			stride_width = face_detector_width // feature_stride
			anchors = create_static_anchors(feature_stride, anchor_total, stride_height, stride_width)
			bounding_box_raw = detection[index + feature_map_channel] * feature_stride
			face_landmark_5_raw = detection[index + feature_map_channel * 2] * feature_stride

			for bounding_box in distance_to_bounding_box(anchors, bounding_box_raw)[keep_indices]:
				bounding_boxes.append(numpy.array(
				[
					bounding_box[0] * ratio_width,
					bounding_box[1] * ratio_height,
					bounding_box[2] * ratio_width,
					bounding_box[3] * ratio_height,
				]))

			for score in detection[index][keep_indices]:
				face_scores.append(score[0])

			for face_landmark_5 in distance_to_face_landmark_5(anchors, face_landmark_5_raw)[keep_indices]:
				face_landmarks_5.append(face_landmark_5 * [ ratio_width, ratio_height ])

	return bounding_boxes, face_scores, face_landmarks_5


def detect_with_yoloface(vision_frame : VisionFrame, face_detector_size : str) -> Tuple[List[BoundingBox], List[Score], List[FaceLandmark5]]:
	bounding_boxes = []
	face_scores = []
	face_landmarks_5 = []
	face_detector_width, face_detector_height = unpack_resolution(face_detector_size)
	temp_vision_frame = resize_frame_resolution(vision_frame, (face_detector_width, face_detector_height))
	ratio_height = vision_frame.shape[0] / temp_vision_frame.shape[0]
	ratio_width = vision_frame.shape[1] / temp_vision_frame.shape[1]
	detect_vision_frame = prepare_detect_frame(temp_vision_frame, face_detector_size)
	detection = forward_with_yoloface(detect_vision_frame)
	detection = numpy.squeeze(detection).T
	bounding_box_raw, score_raw, face_landmark_5_raw = numpy.split(detection, [ 4, 5 ], axis = 1)
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

		face_scores = score_raw.ravel().tolist()
		face_landmark_5_raw[:, 0::3] = (face_landmark_5_raw[:, 0::3]) * ratio_width
		face_landmark_5_raw[:, 1::3] = (face_landmark_5_raw[:, 1::3]) * ratio_height

		for face_landmark_5 in face_landmark_5_raw:
			face_landmarks_5.append(numpy.array(face_landmark_5.reshape(-1, 3)[:, :2]))

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


def forward_with_yoloface(detect_vision_frame : VisionFrame) -> Detection:
	face_detector = get_inference_pool().get('yoloface')

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
	detect_vision_frame = (detect_vision_frame - 127.5) / 128.0
	detect_vision_frame = numpy.expand_dims(detect_vision_frame.transpose(2, 0, 1), axis = 0).astype(numpy.float32)
	return detect_vision_frame
