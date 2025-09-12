from argparse import ArgumentParser

import cv2
import numpy

import facefusion.jobs.job_manager
import facefusion.jobs.job_store
from facefusion import config, content_analyser, face_classifier, face_detector, face_landmarker, face_masker, face_recognizer, logger, state_manager, video_manager, wording
from facefusion.face_analyser import scale_face
from facefusion.face_helper import warp_face_by_face_landmark_5
from facefusion.face_masker import create_area_mask, create_box_mask, create_occlusion_mask, create_region_mask
from facefusion.face_selector import select_faces
from facefusion.filesystem import in_directory, is_image, is_video, same_file_extension
from facefusion.processors import choices as processors_choices
from facefusion.processors.types import FaceDebuggerInputs
from facefusion.program_helper import find_argument_group
from facefusion.types import ApplyStateItem, Args, Face, InferencePool, ProcessMode, VisionFrame
from facefusion.vision import read_static_image, read_static_video_frame


def get_inference_pool() -> InferencePool:
	pass


def clear_inference_pool() -> None:
	pass


def register_args(program : ArgumentParser) -> None:
	group_processors = find_argument_group(program, 'processors')
	if group_processors:
		group_processors.add_argument('--face-debugger-items', help = wording.get('help.face_debugger_items').format(choices = ', '.join(processors_choices.face_debugger_items)), default = config.get_str_list('processors', 'face_debugger_items', 'face-landmark-5/68 face-mask'), choices = processors_choices.face_debugger_items, nargs = '+', metavar = 'FACE_DEBUGGER_ITEMS')
		facefusion.jobs.job_store.register_step_keys([ 'face_debugger_items' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('face_debugger_items', args.get('face_debugger_items'))


def pre_check() -> bool:
	return True


def pre_process(mode : ProcessMode) -> bool:
	if mode in [ 'output', 'preview' ] and not is_image(state_manager.get_item('target_path')) and not is_video(state_manager.get_item('target_path')):
		logger.error(wording.get('choose_image_or_video_target') + wording.get('exclamation_mark'), __name__)
		return False
	if mode == 'output' and not in_directory(state_manager.get_item('output_path')):
		logger.error(wording.get('specify_image_or_video_output') + wording.get('exclamation_mark'), __name__)
		return False
	if mode == 'output' and not same_file_extension(state_manager.get_item('target_path'), state_manager.get_item('output_path')):
		logger.error(wording.get('match_target_and_output_extension') + wording.get('exclamation_mark'), __name__)
		return False
	return True


def post_process() -> None:
	read_static_image.cache_clear()
	read_static_video_frame.cache_clear()
	video_manager.clear_video_pool()
	if state_manager.get_item('video_memory_strategy') == 'strict':
		content_analyser.clear_inference_pool()
		face_classifier.clear_inference_pool()
		face_detector.clear_inference_pool()
		face_landmarker.clear_inference_pool()
		face_masker.clear_inference_pool()
		face_recognizer.clear_inference_pool()


def debug_face(target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	face_debugger_items = state_manager.get_item('face_debugger_items')

	if 'bounding-box' in face_debugger_items:
		temp_vision_frame = draw_bounding_box(target_face, temp_vision_frame)

	if 'face-mask' in face_debugger_items:
		temp_vision_frame = draw_face_mask(target_face, temp_vision_frame)

	if 'face-landmark-5' in face_debugger_items:
		temp_vision_frame = draw_face_landmark_5(target_face, temp_vision_frame)

	if 'face-landmark-5/68' in face_debugger_items:
		temp_vision_frame = draw_face_landmark_5_68(target_face, temp_vision_frame)

	if 'face-landmark-68' in face_debugger_items:
		temp_vision_frame = draw_face_landmark_68(target_face, temp_vision_frame)

	if 'face-landmark-68/5' in face_debugger_items:
		temp_vision_frame = draw_face_landmark_68_5(target_face, temp_vision_frame)

	return temp_vision_frame


def draw_bounding_box(target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	box_color = 0, 0, 255
	border_color = 100, 100, 255
	bounding_box = target_face.bounding_box.astype(numpy.int32)
	x1, y1, x2, y2 = bounding_box

	cv2.rectangle(temp_vision_frame, (x1, y1), (x2, y2), box_color, 2)

	if target_face.angle == 0:
		cv2.line(temp_vision_frame, (x1, y1), (x2, y1), border_color, 3)
	if target_face.angle == 180:
		cv2.line(temp_vision_frame, (x1, y2), (x2, y2), border_color, 3)
	if target_face.angle == 90:
		cv2.line(temp_vision_frame, (x2, y1), (x2, y2), border_color, 3)
	if target_face.angle == 270:
		cv2.line(temp_vision_frame, (x1, y1), (x1, y2), border_color, 3)

	return temp_vision_frame


def draw_face_mask(target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	crop_masks = []
	face_landmark_5 = target_face.landmark_set.get('5')
	face_landmark_68 = target_face.landmark_set.get('68')
	face_landmark_5_68 = target_face.landmark_set.get('5/68')
	crop_vision_frame, affine_matrix = warp_face_by_face_landmark_5(temp_vision_frame, face_landmark_5_68, 'arcface_128', (512, 512))
	inverse_matrix = cv2.invertAffineTransform(affine_matrix)
	temp_size = temp_vision_frame.shape[:2][::-1]
	mask_color = 0, 255, 0

	if numpy.array_equal(face_landmark_5, face_landmark_5_68):
		mask_color = 255, 255, 0

	if 'box' in state_manager.get_item('face_mask_types'):
		box_mask = create_box_mask(crop_vision_frame, 0, state_manager.get_item('face_mask_padding'))
		crop_masks.append(box_mask)

	if 'occlusion' in state_manager.get_item('face_mask_types'):
		occlusion_mask = create_occlusion_mask(crop_vision_frame)
		crop_masks.append(occlusion_mask)

	if 'area' in state_manager.get_item('face_mask_types'):
		face_landmark_68 = cv2.transform(face_landmark_68.reshape(1, -1, 2), affine_matrix).reshape(-1, 2)
		area_mask = create_area_mask(crop_vision_frame, face_landmark_68, state_manager.get_item('face_mask_areas'))
		crop_masks.append(area_mask)

	if 'region' in state_manager.get_item('face_mask_types'):
		region_mask = create_region_mask(crop_vision_frame, state_manager.get_item('face_mask_regions'))
		crop_masks.append(region_mask)

	crop_mask = numpy.minimum.reduce(crop_masks).clip(0, 1)
	crop_mask = (crop_mask * 255).astype(numpy.uint8)
	inverse_vision_frame = cv2.warpAffine(crop_mask, inverse_matrix, temp_size)
	inverse_vision_frame = cv2.threshold(inverse_vision_frame, 100, 255, cv2.THRESH_BINARY)[1]
	inverse_contours, _ = cv2.findContours(inverse_vision_frame, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
	cv2.drawContours(temp_vision_frame, inverse_contours, -1, mask_color, 2)

	return temp_vision_frame


def draw_face_landmark_5(target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	face_landmark_5 = target_face.landmark_set.get('5')
	point_color = 0, 0, 255

	if numpy.any(face_landmark_5):
		face_landmark_5 = face_landmark_5.astype(numpy.int32)

		for point in face_landmark_5:
			cv2.circle(temp_vision_frame, tuple(point), 3, point_color, -1)

	return temp_vision_frame


def draw_face_landmark_5_68(target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	face_landmark_5 = target_face.landmark_set.get('5')
	face_landmark_5_68 = target_face.landmark_set.get('5/68')
	point_color = 0, 255, 0

	if numpy.array_equal(face_landmark_5, face_landmark_5_68):
		point_color = 255, 255, 0

	if numpy.any(face_landmark_5_68):
		face_landmark_5_68 = face_landmark_5_68.astype(numpy.int32)

		for point in face_landmark_5_68:
			cv2.circle(temp_vision_frame, tuple(point), 3, point_color, -1)

	return temp_vision_frame


def draw_face_landmark_68(target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	face_landmark_68 = target_face.landmark_set.get('68')
	face_landmark_68_5 = target_face.landmark_set.get('68/5')
	point_color = 0, 255, 0

	if numpy.array_equal(face_landmark_68, face_landmark_68_5):
		point_color = 255, 255, 0

	if numpy.any(face_landmark_68):
		face_landmark_68 = face_landmark_68.astype(numpy.int32)

		for point in face_landmark_68:
			cv2.circle(temp_vision_frame, tuple(point), 3, point_color, -1)

	return temp_vision_frame


def draw_face_landmark_68_5(target_face : Face, temp_vision_frame : VisionFrame) -> VisionFrame:
	face_landmark_68_5 = target_face.landmark_set.get('68/5')
	point_color = 255, 255, 0

	if numpy.any(face_landmark_68_5):
		face_landmark_68_5 = face_landmark_68_5.astype(numpy.int32)

		for point in face_landmark_68_5:
			cv2.circle(temp_vision_frame, tuple(point), 3, point_color, -1)

	return temp_vision_frame


def process_frame(inputs : FaceDebuggerInputs) -> VisionFrame:
	reference_vision_frame = inputs.get('reference_vision_frame')
	target_vision_frame = inputs.get('target_vision_frame')
	temp_vision_frame = inputs.get('temp_vision_frame')
	target_faces = select_faces(reference_vision_frame, target_vision_frame)

	if target_faces:
		for target_face in target_faces:
			target_face = scale_face(target_face, target_vision_frame, temp_vision_frame)
			temp_vision_frame = debug_face(target_face, temp_vision_frame)

	return temp_vision_frame


