from typing import Any, Tuple
from functools import lru_cache
from time import sleep
import threading
import scipy
import numpy
import onnxruntime

import facefusion.globals
from facefusion import process_manager
from facefusion.typing import ModelSet, AudioChunk, Audio
from facefusion.execution import apply_execution_provider_options
from facefusion.filesystem import resolve_relative_path, is_file
from facefusion.download import conditional_download

VOICE_EXTRACTOR = None
THREAD_SEMAPHORE : threading.Semaphore = threading.Semaphore()
THREAD_LOCK : threading.Lock = threading.Lock()
MODELS : ModelSet =\
{
	'voice_extractor':
	{
		'url': 'https://github.com/facefusion/facefusion-assets/releases/download/models/voice_extractor.onnx',
		'path': resolve_relative_path('../.assets/models/voice_extractor.onnx')
	}
}


def get_voice_extractor() -> Any:
	global VOICE_EXTRACTOR

	with THREAD_LOCK:
		while process_manager.is_checking():
			sleep(0.5)
		if VOICE_EXTRACTOR is None:
			model_path = MODELS.get('voice_extractor').get('path')
			VOICE_EXTRACTOR = onnxruntime.InferenceSession(model_path, providers = apply_execution_provider_options(facefusion.globals.execution_providers))
	return VOICE_EXTRACTOR


def clear_voice_extractor() -> None:
	global VOICE_EXTRACTOR

	VOICE_EXTRACTOR = None


def pre_check() -> bool:
	download_directory_path = resolve_relative_path('../.assets/models')
	model_url = MODELS.get('voice_extractor').get('url')
	model_path = MODELS.get('voice_extractor').get('path')

	if not facefusion.globals.skip_download:
		process_manager.check()
		conditional_download(download_directory_path, [ model_url ])
		process_manager.end()
	return is_file(model_path)


@lru_cache(maxsize = None)
def create_static_hanning_window(filter_size : int) -> Any:
	window = scipy.signal.windows.hann(filter_size, sym = False)
	return window


def batch_extract_voice(audio : Audio, chunk_size : int, overlap_size : float) -> Audio:
	step_size = int(chunk_size * (1 - overlap_size))
	audio_total = numpy.zeros((audio.shape[0], 2)).astype(numpy.float32)
	chunk_total = numpy.zeros((audio.shape[0], 2)).astype(numpy.float32)

	for start in range(0, audio.shape[0], step_size):
		end = min(start + chunk_size, audio.shape[0])
		audio_total[start:end, ...] += extract_voice(audio[start:end, ...])
		chunk_total[start:end, ...] += 1
	audio = audio_total / chunk_total
	return audio


def extract_voice(audio_chunk : AudioChunk) -> AudioChunk:
	voice_extractor = get_voice_extractor()
	extractor_shape = voice_extractor.get_inputs()[0].shape[1:]
	hop_length = 1024
	filter_size = 7680
	trim_size = filter_size // 2
	frequency_bins = trim_size + 1
	chunk_size = hop_length * (extractor_shape[2] - 1)
	audio_chunk, pad_size = prepare_audio_chunk(audio_chunk, chunk_size, trim_size)
	audio_chunk = decompose_audio_chunk(audio_chunk, filter_size, hop_length, frequency_bins, extractor_shape)
	with THREAD_SEMAPHORE:
		audio_chunk = voice_extractor.run(None,
		{
			voice_extractor.get_inputs()[0].name: audio_chunk
		})[0]
	audio_chunk = compose_audio_chunk(audio_chunk, filter_size, hop_length, frequency_bins, extractor_shape)
	audio_chunk = normalize_audio_chunk(audio_chunk, chunk_size, trim_size, pad_size)
	return audio_chunk


def prepare_audio_chunk(audio_chunk : AudioChunk, chunk_size : int, trim_size : int) -> Tuple[AudioChunk, int]:
	audio_chunk = audio_chunk.T
	step_size = chunk_size - 2 * trim_size
	pad_size = step_size - audio_chunk.shape[1] % step_size
	audio_chunk_size = audio_chunk.shape[1] + pad_size
	audio_chunk = audio_chunk.astype(numpy.float32) / numpy.iinfo(numpy.int16).max
	audio_chunk = numpy.pad(audio_chunk, ((0, 0), (trim_size, trim_size + pad_size)), mode = 'constant', constant_values = 0)
	temp_audio_chunks = []

	for index in range(0, audio_chunk_size, step_size):
		chunk = audio_chunk[:, index:index + chunk_size]
		temp_audio_chunks.append(chunk)
	audio_chunk = numpy.concatenate(temp_audio_chunks, axis = 0)
	audio_chunk = audio_chunk.reshape((-1, chunk_size))
	return audio_chunk, pad_size


def decompose_audio_chunk(audio_chunk : AudioChunk, filter_size : int, hop_length : int, frequency_bins : int, extractor_shape : Tuple[int, int, int]) -> AudioChunk:
	window = create_static_hanning_window(filter_size)
	audio_chunk = scipy.signal.stft(audio_chunk, nperseg = filter_size, noverlap = filter_size - hop_length, window = window, padded = False)[2]
	audio_chunk = numpy.stack((numpy.real(audio_chunk), numpy.imag(audio_chunk)), axis = -1).transpose((0, 3, 1, 2))
	audio_chunk = audio_chunk.reshape((-1, 2, 2, frequency_bins, extractor_shape[2])).reshape((-1, extractor_shape[0], frequency_bins, extractor_shape[2]))
	audio_chunk = audio_chunk[:,:,:extractor_shape[1]]
	audio_chunk /= numpy.sqrt(1.0 / window.sum() ** 2)
	return audio_chunk


def compose_audio_chunk(audio_chunk : AudioChunk, filter_size : int, hop_length : int, frequency_bins : int, extractor_shape : Tuple[int, int, int]) -> AudioChunk:
	window = create_static_hanning_window(filter_size)
	audio_chunk = numpy.pad(audio_chunk, ((0, 0), (0, 0), (0, frequency_bins - extractor_shape[1]), (0, 0)), mode = 'constant')
	audio_chunk = audio_chunk.reshape(-1, 2, frequency_bins, extractor_shape[2]).transpose((0, 2, 3, 1))
	audio_chunk = audio_chunk[:,:,:,0] + 1j * audio_chunk[:,:,:,1]
	audio_chunk = scipy.signal.istft(audio_chunk, nperseg = filter_size, noverlap = filter_size - hop_length, window = window)[1]
	audio_chunk *= numpy.sqrt(1.0 / window.sum() ** 2)
	return audio_chunk


def normalize_audio_chunk(audio_chunk : AudioChunk, chunk_size : int, trim_size : int, pad_size : int) -> AudioChunk:
	audio_chunk = audio_chunk.reshape((-1, 2, chunk_size))
	audio_chunk = audio_chunk[:,:,trim_size:-trim_size].transpose(1, 0, 2)
	audio_chunk = audio_chunk.reshape(2, -1)[:,:-pad_size].T
	return audio_chunk
