from functools import lru_cache
from typing import Tuple

import numpy
import scipy

from facefusion import inference_manager
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.filesystem import resolve_relative_path
from facefusion.thread_helper import thread_semaphore
from facefusion.types import Audio, AudioChunk, DownloadScope, InferencePool, ModelOptions, ModelSet


@lru_cache(maxsize = None)
def create_static_model_set(download_scope : DownloadScope) -> ModelSet:
	return\
	{
		'kim_vocal_2':
		{
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
		}
	}


def get_inference_pool() -> InferencePool:
	model_names = [ 'kim_vocal_2' ]
	model_source_set = get_model_options().get('sources')

	return inference_manager.get_inference_pool(__name__, model_names, model_source_set)


def clear_inference_pool() -> None:
	model_names = [ 'kim_vocal_2' ]
	inference_manager.clear_inference_pool(__name__, model_names)


def get_model_options() -> ModelOptions:
	return create_static_model_set('full').get('kim_vocal_2')


def pre_check() -> bool:
	model_hash_set = get_model_options().get('hashes')
	model_source_set = get_model_options().get('sources')

	return conditional_download_hashes(model_hash_set) and conditional_download_sources(model_source_set)


def batch_extract_voice(audio : Audio, chunk_size : int, step_size : int) -> Audio:
	temp_audio = numpy.zeros((audio.shape[0], 2)).astype(numpy.float32)
	temp_chunk = numpy.zeros((audio.shape[0], 2)).astype(numpy.float32)

	for start in range(0, audio.shape[0], step_size):
		end = min(start + chunk_size, audio.shape[0])
		temp_audio[start:end, ...] += extract_voice(audio[start:end, ...])
		temp_chunk[start:end, ...] += 1

	audio = temp_audio / temp_chunk
	return audio


def extract_voice(temp_audio_chunk : AudioChunk) -> AudioChunk:
	voice_extractor = get_inference_pool().get('voice_extractor')
	chunk_size = (voice_extractor.get_inputs()[0].shape[3] - 1) * 1024
	trim_size = 3840
	temp_audio_chunk, pad_size = prepare_audio_chunk(temp_audio_chunk.T, chunk_size, trim_size)
	temp_audio_chunk = decompose_audio_chunk(temp_audio_chunk, trim_size)
	temp_audio_chunk = forward(temp_audio_chunk)
	temp_audio_chunk = compose_audio_chunk(temp_audio_chunk, trim_size)
	temp_audio_chunk = normalize_audio_chunk(temp_audio_chunk, chunk_size, trim_size, pad_size)
	return temp_audio_chunk


def forward(temp_audio_chunk : AudioChunk) -> AudioChunk:
	voice_extractor = get_inference_pool().get('voice_extractor')

	with thread_semaphore():
		temp_audio_chunk = voice_extractor.run(None,
		{
			'input': temp_audio_chunk
		})[0]

	return temp_audio_chunk


def prepare_audio_chunk(temp_audio_chunk : AudioChunk, chunk_size : int, trim_size : int) -> Tuple[AudioChunk, int]:
	step_size = chunk_size - 2 * trim_size
	pad_size = step_size - temp_audio_chunk.shape[1] % step_size
	audio_chunk_size = temp_audio_chunk.shape[1] + pad_size
	temp_audio_chunk = temp_audio_chunk.astype(numpy.float32) / numpy.iinfo(numpy.int16).max
	temp_audio_chunk = numpy.pad(temp_audio_chunk, ((0, 0), (trim_size, trim_size + pad_size)))
	temp_audio_chunks = []

	for index in range(0, audio_chunk_size, step_size):
		temp_audio_chunks.append(temp_audio_chunk[:, index:index + chunk_size])

	temp_audio_chunk = numpy.concatenate(temp_audio_chunks, axis = 0)
	temp_audio_chunk = temp_audio_chunk.reshape((-1, chunk_size))
	return temp_audio_chunk, pad_size


def decompose_audio_chunk(temp_audio_chunk : AudioChunk, trim_size : int) -> AudioChunk:
	frame_size = 7680
	frame_overlap = 6656
	frame_total = 3072
	bin_total = 256
	channel_total = 4
	window = scipy.signal.windows.hann(frame_size)
	temp_audio_chunk = scipy.signal.stft(temp_audio_chunk, nperseg = frame_size, noverlap = frame_overlap, window = window)[2]
	temp_audio_chunk = numpy.stack((numpy.real(temp_audio_chunk), numpy.imag(temp_audio_chunk)), axis = -1).transpose((0, 3, 1, 2))
	temp_audio_chunk = temp_audio_chunk.reshape(-1, 2, 2, trim_size + 1, bin_total).reshape(-1, channel_total, trim_size + 1, bin_total)
	temp_audio_chunk = temp_audio_chunk[:, :, :frame_total]
	temp_audio_chunk /= numpy.sqrt(1.0 / window.sum() ** 2)
	return temp_audio_chunk


def compose_audio_chunk(temp_audio_chunk : AudioChunk, trim_size : int) -> AudioChunk:
	frame_size = 7680
	frame_overlap = 6656
	frame_total = 3072
	bin_total = 256
	window = scipy.signal.windows.hann(frame_size)
	temp_audio_chunk = numpy.pad(temp_audio_chunk, ((0, 0), (0, 0), (0, trim_size + 1 - frame_total), (0, 0)))
	temp_audio_chunk = temp_audio_chunk.reshape(-1, 2, trim_size + 1, bin_total).transpose((0, 2, 3, 1))
	temp_audio_chunk = temp_audio_chunk[:, :, :, 0] + 1j * temp_audio_chunk[:, :, :, 1]
	temp_audio_chunk = scipy.signal.istft(temp_audio_chunk, nperseg = frame_size, noverlap = frame_overlap, window = window)[1]
	temp_audio_chunk *= numpy.sqrt(1.0 / window.sum() ** 2)
	return temp_audio_chunk


def normalize_audio_chunk(temp_audio_chunk : AudioChunk, chunk_size : int, trim_size : int, pad_size : int) -> AudioChunk:
	temp_audio_chunk = temp_audio_chunk.reshape((-1, 2, chunk_size))
	temp_audio_chunk = temp_audio_chunk[:, :, trim_size:-trim_size].transpose(1, 0, 2)
	temp_audio_chunk = temp_audio_chunk.reshape(2, -1)[:, :-pad_size].T
	return temp_audio_chunk
