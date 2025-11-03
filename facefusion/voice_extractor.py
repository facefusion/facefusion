from functools import lru_cache
from typing import Tuple

import numpy
import scipy

from facefusion import inference_manager, state_manager
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.filesystem import resolve_relative_path
from facefusion.thread_helper import thread_semaphore
from facefusion.types import Audio, AudioChunk, DownloadScope, DownloadSet, InferencePool, ModelSet, Voice, VoiceChunk


@lru_cache()
def create_static_model_set(download_scope : DownloadScope) -> ModelSet:
	return\
	{
		'kim_vocal_1':
		{
			'__metadata__':
			{
				'vendor': 'KimberleyJensen',
				'license': 'Non-Commercial',
				'year': 2023
			},
			'hashes':
			{
				'voice_extractor':
				{
					'url': resolve_download_url('models-3.4.0', 'kim_vocal_1.hash'),
					'path': resolve_relative_path('../.assets/models/kim_vocal_1.hash')
				}
			},
			'sources':
			{
				'voice_extractor':
				{
					'url': resolve_download_url('models-3.4.0', 'kim_vocal_1.onnx'),
					'path': resolve_relative_path('../.assets/models/kim_vocal_1.onnx')
				}
			}
		},
		'kim_vocal_2':
		{
			'__metadata__':
			{
				'vendor': 'KimberleyJensen',
				'license': 'Non-Commercial',
				'year': 2023
			},
			'hashes':
			{
				'voice_extractor':
				{
					'url': resolve_download_url('models-3.0.0', 'kim_vocal_2.hash'),
					'path': resolve_relative_path('../.assets/models/kim_vocal_2.hash')
				}
			},
			'sources':
			{
				'voice_extractor':
				{
					'url': resolve_download_url('models-3.0.0', 'kim_vocal_2.onnx'),
					'path': resolve_relative_path('../.assets/models/kim_vocal_2.onnx')
				}
			}
		},
		'uvr_mdxnet':
		{
			'__metadata__':
			{
				'vendor': 'Unknown',
				'license': 'Non-Commercial',
				'year': 2023
			},
			'hashes':
			{
				'voice_extractor':
				{
					'url': resolve_download_url('models-3.4.0', 'uvr_mdxnet.hash'),
					'path': resolve_relative_path('../.assets/models/uvr_mdxnet.hash')
				}
			},
			'sources':
			{
				'voice_extractor':
				{
					'url': resolve_download_url('models-3.4.0', 'uvr_mdxnet.onnx'),
					'path': resolve_relative_path('../.assets/models/uvr_mdxnet.onnx')
				}
			}
		}
	}


def get_inference_pool() -> InferencePool:
	model_names = [ state_manager.get_item('voice_extractor_model') ]
	_, model_source_set = collect_model_downloads()

	return inference_manager.get_inference_pool(__name__, model_names, model_source_set)


def clear_inference_pool() -> None:
	model_names = [ state_manager.get_item('voice_extractor_model') ]
	inference_manager.clear_inference_pool(__name__, model_names)


def collect_model_downloads() -> Tuple[DownloadSet, DownloadSet]:
	model_set = create_static_model_set('full')
	model_hash_set = {}
	model_source_set = {}

	for voice_extractor_model in [ 'kim_vocal_1', 'kim_vocal_2', 'uvr_mdxnet' ]:
		if state_manager.get_item('voice_extractor_model') == voice_extractor_model:
			model_hash_set[voice_extractor_model] = model_set.get(voice_extractor_model).get('hashes').get('voice_extractor')
			model_source_set[voice_extractor_model] = model_set.get(voice_extractor_model).get('sources').get('voice_extractor')

	return model_hash_set, model_source_set


def pre_check() -> bool:
	model_hash_set, model_source_set = collect_model_downloads()

	return conditional_download_hashes(model_hash_set) and conditional_download_sources(model_source_set)


def batch_extract_voice(audio : Audio, chunk_size : int, step_size : int) -> Voice:
	temp_voice = numpy.zeros((audio.shape[0], 2)).astype(numpy.float32)
	temp_voice_chunk = numpy.zeros((audio.shape[0], 2)).astype(numpy.float32)

	for start in range(0, audio.shape[0], step_size):
		end = min(start + chunk_size, audio.shape[0])
		temp_voice[start:end, ...] += extract_voice(audio[start:end, ...])
		temp_voice_chunk[start:end, ...] += 1

	voice = temp_voice / temp_voice_chunk
	return voice


def extract_voice(temp_audio_chunk : AudioChunk) -> VoiceChunk:
	voice_extractor = get_inference_pool().get(state_manager.get_item('voice_extractor_model'))
	voice_trim_size = 3840
	voice_chunk_size = (voice_extractor.get_inputs()[0].shape[3] - 1) * 1024
	temp_audio_chunk, audio_pad_size = prepare_audio_chunk(temp_audio_chunk.T, voice_chunk_size, voice_trim_size)
	temp_audio_chunk = decompose_audio_chunk(temp_audio_chunk, voice_trim_size)
	temp_audio_chunk = forward(temp_audio_chunk)
	temp_audio_chunk = compose_audio_chunk(temp_audio_chunk, voice_trim_size)
	temp_audio_chunk = normalize_audio_chunk(temp_audio_chunk, voice_chunk_size, voice_trim_size, audio_pad_size)
	return temp_audio_chunk


def forward(temp_audio_chunk : AudioChunk) -> AudioChunk:
	voice_extractor = get_inference_pool().get(state_manager.get_item('voice_extractor_model'))

	with thread_semaphore():
		temp_audio_chunk = voice_extractor.run(None,
		{
			'input': temp_audio_chunk
		})[0]

	return temp_audio_chunk


def prepare_audio_chunk(temp_audio_chunk : AudioChunk, chunk_size : int, audio_trim_size : int) -> Tuple[AudioChunk, int]:
	audio_step_size = chunk_size - 2 * audio_trim_size
	audio_pad_size = audio_step_size - temp_audio_chunk.shape[1] % audio_step_size
	audio_chunk_size = temp_audio_chunk.shape[1] + audio_pad_size
	temp_audio_chunk = temp_audio_chunk.astype(numpy.float32) / numpy.iinfo(numpy.int16).max
	temp_audio_chunk = numpy.pad(temp_audio_chunk, ((0, 0), (audio_trim_size, audio_trim_size + audio_pad_size)))
	temp_audio_chunks = []

	for index in range(0, audio_chunk_size, audio_step_size):
		temp_audio_chunks.append(temp_audio_chunk[:, index:index + chunk_size])

	temp_audio_chunk = numpy.concatenate(temp_audio_chunks, axis = 0)
	temp_audio_chunk = temp_audio_chunk.reshape((-1, chunk_size))
	return temp_audio_chunk, audio_pad_size


def decompose_audio_chunk(temp_audio_chunk : AudioChunk, audio_trim_size : int) -> AudioChunk:
	audio_frame_size = 7680
	audio_frame_overlap = 6656
	audio_frame_total = 3072
	audio_bin_total = 256
	audio_channel_total = 4
	window = scipy.signal.windows.hann(audio_frame_size)
	temp_audio_chunk = scipy.signal.stft(temp_audio_chunk, nperseg = audio_frame_size, noverlap = audio_frame_overlap, window = window)[2]
	temp_audio_chunk = numpy.stack((numpy.real(temp_audio_chunk), numpy.imag(temp_audio_chunk)), axis = -1).transpose((0, 3, 1, 2))
	temp_audio_chunk = temp_audio_chunk.reshape(-1, 2, 2, audio_trim_size + 1, audio_bin_total).reshape(-1, audio_channel_total, audio_trim_size + 1, audio_bin_total)
	temp_audio_chunk = temp_audio_chunk[:, :, :audio_frame_total]
	temp_audio_chunk /= numpy.sqrt(1.0 / window.sum() ** 2)
	return temp_audio_chunk


def compose_audio_chunk(temp_audio_chunk : AudioChunk, audio_trim_size : int) -> AudioChunk:
	audio_frame_size = 7680
	audio_frame_overlap = 6656
	audio_frame_total = 3072
	audio_bin_total = 256
	window = scipy.signal.windows.hann(audio_frame_size)
	temp_audio_chunk = numpy.pad(temp_audio_chunk, ((0, 0), (0, 0), (0, audio_trim_size + 1 - audio_frame_total), (0, 0)))
	temp_audio_chunk = temp_audio_chunk.reshape(-1, 2, audio_trim_size + 1, audio_bin_total).transpose((0, 2, 3, 1))
	temp_audio_chunk = temp_audio_chunk[:, :, :, 0] + 1j * temp_audio_chunk[:, :, :, 1]
	temp_audio_chunk = scipy.signal.istft(temp_audio_chunk, nperseg = audio_frame_size, noverlap = audio_frame_overlap, window = window)[1]
	temp_audio_chunk *= numpy.sqrt(1.0 / window.sum() ** 2)
	return temp_audio_chunk


def normalize_audio_chunk(temp_audio_chunk : AudioChunk, chunk_size : int, audio_trim_size : int, audio_pad_size : int) -> AudioChunk:
	temp_audio_chunk = temp_audio_chunk.reshape((-1, 2, chunk_size))
	temp_audio_chunk = temp_audio_chunk[:, :, audio_trim_size:-audio_trim_size].transpose(1, 0, 2)
	temp_audio_chunk = temp_audio_chunk.reshape(2, -1)[:, :-audio_pad_size].T
	return temp_audio_chunk
