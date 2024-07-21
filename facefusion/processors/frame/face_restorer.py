from time import sleep
from typing import Any, Tuple

import cv2
import numpy

from facefusion import process_manager, state_manager
from facefusion.download import conditional_download
from facefusion.execution import create_inference_session
from facefusion.face_masker import create_face_mask
from facefusion.filesystem import is_file, resolve_relative_path
from facefusion.thread_helper import conditional_thread_semaphore, thread_lock
from facefusion.typing import ModelSet, VisionFrame

EXPRESSION_RESTORER = None
MODELS : ModelSet =\
{
	'live_portrait_expression_restorer':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/live_portrait_expression_restorer.onnx',
		'path': resolve_relative_path('../.assets/models/live_portrait_expression_restorer.onnx'),
	}
}


def get_expression_restorer() -> Any:
	global EXPRESSION_RESTORER

	with thread_lock():
		while process_manager.is_checking():
			sleep(0.5)
		if EXPRESSION_RESTORER is None:
			model_path = MODELS.get('live_portrait_expression_restorer').get('path')
			EXPRESSION_RESTORER = create_inference_session(model_path, state_manager.get_item('execution_device_id'), state_manager.get_item('execution_providers'))
	return EXPRESSION_RESTORER


def clear_expression_restorer() -> None:
	global EXPRESSION_RESTORER

	EXPRESSION_RESTORER = None


def pre_check() -> bool:
	download_directory_path = resolve_relative_path('../.assets/models')
	model_urls =\
	[
		MODELS.get('live_portrait_expression_restorer').get('url'),
	]
	model_paths =\
	[
		MODELS.get('live_portrait_expression_restorer').get('path'),
	]

	if not state_manager.get_item('skip_download'):
		process_manager.check()
		conditional_download(download_directory_path, model_urls)
		process_manager.end()
	return all(is_file(model_path) for model_path in model_paths)


def restore_expression(source_vision_frame : VisionFrame, target_vision_frame : VisionFrame, restore_amount : float) -> Tuple[VisionFrame, float]:
	expression_restorer = get_expression_restorer()
	prepare_source_frame = cv2.resize(source_vision_frame, (512, 512))[:, :, ::-1].transpose(2, 0, 1).astype(numpy.float32) / 255
	prepare_target_frame = cv2.resize(target_vision_frame, (512, 512))[:, :, ::-1].transpose(2, 0, 1).astype(numpy.float32) / 255
	prepare_restore_amount = numpy.array(restore_amount).astype(numpy.float32)

	with conditional_thread_semaphore():
		restore_frame : VisionFrame = expression_restorer.run(None,
		{
			'source': [ prepare_source_frame ],
			'target': [ prepare_target_frame ],
			'intensity': prepare_restore_amount
		})[0][0]

	restore_frame = restore_frame.transpose(1, 2, 0)[:, :, ::-1].clip(0, 1) * 255
	restore_frame = restore_frame.astype(target_vision_frame.dtype)
	face_mask = create_face_mask(restore_frame)[:, :, numpy.newaxis].repeat(3, axis = 2)
	restore_frame = restore_frame * face_mask + cv2.resize(target_vision_frame, restore_frame.shape[:2][::-1]) * (1 - face_mask)
	matrix_scale = restore_frame.shape[1] / target_vision_frame.shape[1]
	return restore_frame, matrix_scale
