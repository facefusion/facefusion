from argparse import ArgumentParser
from functools import lru_cache

import cv2
import numpy

import facefusion.jobs.job_manager
import facefusion.jobs.job_store
from facefusion import config, content_analyser, face_classifier, face_detector, face_landmarker, face_masker, face_recognizer, inference_manager, logger, state_manager, video_manager, voice_extractor, wording
from facefusion.audio import read_static_voice
from facefusion.common_helper import create_float_metavar
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.face_analyser import scale_face
from facefusion.face_helper import create_bounding_box, paste_back, warp_face_by_bounding_box, warp_face_by_face_landmark_5
from facefusion.face_masker import create_area_mask, create_box_mask, create_occlusion_mask
from facefusion.face_selector import select_faces
from facefusion.filesystem import has_audio, resolve_relative_path
from facefusion.processors import choices as processors_choices
from facefusion.processors.types import LipSyncerInputs, LipSyncerWeight
from facefusion.program_helper import find_argument_group
from facefusion.thread_helper import conditional_thread_semaphore
from facefusion.types import ApplyStateItem, Args, AudioFrame, DownloadScope, Face, InferencePool, ModelOptions, ModelSet, ProcessMode, VisionFrame
from facefusion.vision import read_static_image, read_static_video_frame


@lru_cache()
def create_static_model_set(download_scope : DownloadScope) -> ModelSet:
	return\
	{
		'edtalk_256':
		{
			'hashes':
			{
				'lip_syncer':
				{
					'url': resolve_download_url('models-3.3.0', 'edtalk_256.hash'),
					'path': resolve_relative_path('../.assets/models/edtalk_256.hash')
				}
			},
			'sources':
			{
				'lip_syncer':
				{
					'url': resolve_download_url('models-3.3.0', 'edtalk_256.onnx'),
					'path': resolve_relative_path('../.assets/models/edtalk_256.onnx')
				}
			},
			'type': 'edtalk',
			'size': (256, 256)
		},
		'wav2lip_96':
		{
			'hashes':
			{
				'lip_syncer':
				{
					'url': resolve_download_url('models-3.0.0', 'wav2lip_96.hash'),
					'path': resolve_relative_path('../.assets/models/wav2lip_96.hash')
				}
			},
			'sources':
			{
				'lip_syncer':
				{
					'url': resolve_download_url('models-3.0.0', 'wav2lip_96.onnx'),
					'path': resolve_relative_path('../.assets/models/wav2lip_96.onnx')
				}
			},
			'type': 'wav2lip',
			'size': (96, 96)
		},
		'wav2lip_gan_96':
		{
			'hashes':
			{
				'lip_syncer':
				{
					'url': resolve_download_url('models-3.0.0', 'wav2lip_gan_96.hash'),
					'path': resolve_relative_path('../.assets/models/wav2lip_gan_96.hash')
				}
			},
			'sources':
			{
				'lip_syncer':
				{
					'url': resolve_download_url('models-3.0.0', 'wav2lip_gan_96.onnx'),
					'path': resolve_relative_path('../.assets/models/wav2lip_gan_96.onnx')
				}
			},
			'type': 'wav2lip',
			'size': (96, 96)
		}
	}


def get_inference_pool() -> InferencePool:
	model_names = [ state_manager.get_item('lip_syncer_model') ]
	model_source_set = get_model_options().get('sources')

	return inference_manager.get_inference_pool(__name__, model_names, model_source_set)


def clear_inference_pool() -> None:
	model_names = [ state_manager.get_item('lip_syncer_model') ]
	inference_manager.clear_inference_pool(__name__, model_names)


def get_model_options() -> ModelOptions:
	model_name = state_manager.get_item('lip_syncer_model')
	return create_static_model_set('full').get(model_name)


def register_args(program : ArgumentParser) -> None:
	group_processors = find_argument_group(program, 'processors')
	if group_processors:
		group_processors.add_argument('--lip-syncer-model', help = wording.get('help.lip_syncer_model'), default = config.get_str_value('processors', 'lip_syncer_model', 'wav2lip_gan_96'), choices = processors_choices.lip_syncer_models)
		group_processors.add_argument('--lip-syncer-weight', help = wording.get('help.lip_syncer_weight'), type = float, default = config.get_float_value('processors', 'lip_syncer_weight', '0.5'), choices = processors_choices.lip_syncer_weight_range, metavar = create_float_metavar(processors_choices.lip_syncer_weight_range))
		facefusion.jobs.job_store.register_step_keys([ 'lip_syncer_model', 'lip_syncer_weight' ])


def apply_args(args : Args, apply_state_item : ApplyStateItem) -> None:
	apply_state_item('lip_syncer_model', args.get('lip_syncer_model'))
	apply_state_item('lip_syncer_weight', args.get('lip_syncer_weight'))


def pre_check() -> bool:
	model_hash_set = get_model_options().get('hashes')
	model_source_set = get_model_options().get('sources')

	return conditional_download_hashes(model_hash_set) and conditional_download_sources(model_source_set)


def pre_process(mode : ProcessMode) -> bool:
	if not has_audio(state_manager.get_item('source_paths')):
		logger.error(wording.get('choose_audio_source') + wording.get('exclamation_mark'), __name__)
		return False
	return True


def post_process() -> None:
	read_static_image.cache_clear()
	read_static_video_frame.cache_clear()
	read_static_voice.cache_clear()
	video_manager.clear_video_pool()
	if state_manager.get_item('video_memory_strategy') in [ 'strict', 'moderate' ]:
		clear_inference_pool()
	if state_manager.get_item('video_memory_strategy') == 'strict':
		content_analyser.clear_inference_pool()
		face_classifier.clear_inference_pool()
		face_detector.clear_inference_pool()
		face_landmarker.clear_inference_pool()
		face_masker.clear_inference_pool()
		face_recognizer.clear_inference_pool()
		voice_extractor.clear_inference_pool()


def sync_lip(target_face : Face, source_voice_frame : AudioFrame, temp_vision_frame : VisionFrame) -> VisionFrame:
	model_type = get_model_options().get('type')
	model_size = get_model_options().get('size')
	source_voice_frame = prepare_audio_frame(source_voice_frame)
	crop_vision_frame, affine_matrix = warp_face_by_face_landmark_5(temp_vision_frame, target_face.landmark_set.get('5/68'), 'ffhq_512', (512, 512))
	crop_masks = []

	if 'occlusion' in state_manager.get_item('face_mask_types'):
		occlusion_mask = create_occlusion_mask(crop_vision_frame)
		crop_masks.append(occlusion_mask)

	if model_type == 'edtalk':
		lip_syncer_weight = numpy.array([ state_manager.get_item('lip_syncer_weight') ]).astype(numpy.float32)
		box_mask = create_box_mask(crop_vision_frame, state_manager.get_item('face_mask_blur'), state_manager.get_item('face_mask_padding'))
		crop_masks.append(box_mask)
		crop_vision_frame = prepare_crop_frame(crop_vision_frame)
		crop_vision_frame = forward_edtalk(source_voice_frame, crop_vision_frame, lip_syncer_weight)
		crop_vision_frame = normalize_crop_frame(crop_vision_frame)

	if model_type == 'wav2lip':
		face_landmark_68 = cv2.transform(target_face.landmark_set.get('68').reshape(1, -1, 2), affine_matrix).reshape(-1, 2)
		area_mask = create_area_mask(crop_vision_frame, face_landmark_68, [ 'lower-face' ])
		crop_masks.append(area_mask)
		bounding_box = create_bounding_box(face_landmark_68)
		area_vision_frame, area_matrix = warp_face_by_bounding_box(crop_vision_frame, bounding_box, model_size)
		area_vision_frame = prepare_crop_frame(area_vision_frame)
		area_vision_frame = forward_wav2lip(source_voice_frame, area_vision_frame)
		area_vision_frame = normalize_crop_frame(area_vision_frame)
		crop_vision_frame = cv2.warpAffine(area_vision_frame, cv2.invertAffineTransform(area_matrix), (512, 512), borderMode = cv2.BORDER_REPLICATE)

	crop_mask = numpy.minimum.reduce(crop_masks)
	paste_vision_frame = paste_back(temp_vision_frame, crop_vision_frame, crop_mask, affine_matrix)
	return paste_vision_frame


def forward_edtalk(temp_audio_frame : AudioFrame, crop_vision_frame : VisionFrame, lip_syncer_weight : LipSyncerWeight) -> VisionFrame:
	lip_syncer = get_inference_pool().get('lip_syncer')

	with conditional_thread_semaphore():
		crop_vision_frame = lip_syncer.run(None,
		{
			'source': temp_audio_frame,
			'target': crop_vision_frame,
			'weight': lip_syncer_weight
		})[0]

	return crop_vision_frame


def forward_wav2lip(temp_audio_frame : AudioFrame, area_vision_frame : VisionFrame) -> VisionFrame:
	lip_syncer = get_inference_pool().get('lip_syncer')

	with conditional_thread_semaphore():
		area_vision_frame = lip_syncer.run(None,
		{
			'source': temp_audio_frame,
			'target': area_vision_frame
		})[0]

	return area_vision_frame


def prepare_audio_frame(temp_audio_frame : AudioFrame) -> AudioFrame:
	model_type = get_model_options().get('type')
	temp_audio_frame = numpy.maximum(numpy.exp(-5 * numpy.log(10)), temp_audio_frame)
	temp_audio_frame = numpy.log10(temp_audio_frame) * 1.6 + 3.2
	temp_audio_frame = temp_audio_frame.clip(-4, 4).astype(numpy.float32)

	if model_type == 'wav2lip':
		temp_audio_frame = temp_audio_frame * state_manager.get_item('lip_syncer_weight') * 2.0

	temp_audio_frame = numpy.expand_dims(temp_audio_frame, axis = (0, 1))
	return temp_audio_frame


def prepare_crop_frame(crop_vision_frame : VisionFrame) -> VisionFrame:
	model_type = get_model_options().get('type')
	model_size = get_model_options().get('size')

	if model_type == 'edtalk':
		crop_vision_frame = cv2.resize(crop_vision_frame, model_size, interpolation = cv2.INTER_AREA)
		crop_vision_frame = crop_vision_frame[:, :, ::-1] / 255.0
		crop_vision_frame = numpy.expand_dims(crop_vision_frame.transpose(2, 0, 1), axis = 0).astype(numpy.float32)

	if model_type == 'wav2lip':
		crop_vision_frame = numpy.expand_dims(crop_vision_frame, axis = 0)
		prepare_vision_frame = crop_vision_frame.copy()
		prepare_vision_frame[:, model_size[0] // 2:] = 0
		crop_vision_frame = numpy.concatenate((prepare_vision_frame, crop_vision_frame), axis = 3)
		crop_vision_frame = crop_vision_frame.transpose(0, 3, 1, 2).astype(numpy.float32) / 255.0

	return crop_vision_frame


def normalize_crop_frame(crop_vision_frame : VisionFrame) -> VisionFrame:
	model_type = get_model_options().get('type')
	crop_vision_frame = crop_vision_frame[0].transpose(1, 2, 0)
	crop_vision_frame = crop_vision_frame.clip(0, 1) * 255
	crop_vision_frame = crop_vision_frame.astype(numpy.uint8)

	if model_type == 'edtalk':
		crop_vision_frame = crop_vision_frame[:, :, ::-1]
		crop_vision_frame = cv2.resize(crop_vision_frame, (512, 512), interpolation = cv2.INTER_CUBIC)

	return crop_vision_frame


def process_frame(inputs : LipSyncerInputs) -> VisionFrame:
	reference_vision_frame = inputs.get('reference_vision_frame')
	source_voice_frame = inputs.get('source_voice_frame')
	target_vision_frame = inputs.get('target_vision_frame')
	temp_vision_frame = inputs.get('temp_vision_frame')
	target_faces = select_faces(reference_vision_frame, target_vision_frame)

	if target_faces:
		for target_face in target_faces:
			target_face = scale_face(target_face, target_vision_frame, temp_vision_frame)
			temp_vision_frame = sync_lip(target_face, source_voice_frame, temp_vision_frame)

	return temp_vision_frame

