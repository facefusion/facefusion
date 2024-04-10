from typing import Any, Tuple
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
	voice_extractor = get_voice_extractor()
	chunk_size = 1024 * (voice_extractor.get_inputs()[0].shape[3] - 1)
	trim_size = 3840
	temp_audio_chunk, pad_size = prepare_audio_chunk(temp_audio_chunk.T, chunk_size, trim_size)
	temp_audio_chunk = decompose_audio_chunk(temp_audio_chunk, trim_size)
	with THREAD_SEMAPHORE:
		temp_audio_chunk = voice_extractor.run(None,
		{
			voice_extractor.get_inputs()[0].name: temp_audio_chunk
		})[0]
	temp_audio_chunk = compose_audio_chunk(temp_audio_chunk, trim_size)
	temp_audio_chunk = normalize_audio_chunk(temp_audio_chunk, chunk_size, trim_size, pad_size)
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
	voice_extractor_shape = get_voice_extractor().get_inputs()[0].shape
	window = scipy.signal.windows.hann(frame_size)
	temp_audio_chunk = scipy.signal.stft(temp_audio_chunk, nperseg = frame_size, noverlap = frame_overlap, window = window)[2]
	temp_audio_chunk = numpy.stack((numpy.real(temp_audio_chunk), numpy.imag(temp_audio_chunk)), axis = -1).transpose((0, 3, 1, 2))
	temp_audio_chunk = temp_audio_chunk.reshape(-1, 2, 2, trim_size + 1, voice_extractor_shape[3]).reshape(-1, voice_extractor_shape[1], trim_size + 1, voice_extractor_shape[3])
	temp_audio_chunk = temp_audio_chunk[:, :, :voice_extractor_shape[2]]
	temp_audio_chunk /= numpy.sqrt(1.0 / window.sum() ** 2)
	return temp_audio_chunk


def compose_audio_chunk(temp_audio_chunk : AudioChunk, trim_size : int) -> AudioChunk:
	frame_size = 7680
	frame_overlap = 6656
	voice_extractor_shape = get_voice_extractor().get_inputs()[0].shape
	window = scipy.signal.windows.hann(frame_size)
	temp_audio_chunk = numpy.pad(temp_audio_chunk, ((0, 0), (0, 0), (0, trim_size + 1 - voice_extractor_shape[2]), (0, 0)))
	temp_audio_chunk = temp_audio_chunk.reshape(-1, 2, trim_size + 1, voice_extractor_shape[3]).transpose((0, 2, 3, 1))
	temp_audio_chunk = temp_audio_chunk[:, :, :, 0] + 1j * temp_audio_chunk[:, :, :, 1]
	temp_audio_chunk = scipy.signal.istft(temp_audio_chunk, nperseg = frame_size, noverlap = frame_overlap, window = window)[1]
	temp_audio_chunk *= numpy.sqrt(1.0 / window.sum() ** 2)
	return temp_audio_chunk


def normalize_audio_chunk(temp_audio_chunk : AudioChunk, chunk_size : int, trim_size : int, pad_size : int) -> AudioChunk:
	temp_audio_chunk = temp_audio_chunk.reshape((-1, 2, chunk_size))
	temp_audio_chunk = temp_audio_chunk[:, :, trim_size:-trim_size].transpose(1, 0, 2)
	temp_audio_chunk = temp_audio_chunk.reshape(2, -1)[:, :-pad_size].T
	return temp_audio_chunk
