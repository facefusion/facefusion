from typing import Optional, Any, List

import numpy
import scipy
from functools import lru_cache
from facefusion.ffmpeg import read_audio_buffer
from facefusion.typing import Fps


def monoize_audio(audio : numpy.ndarray[Any, Any]) -> numpy.ndarray[Any, Any]:
	if audio.ndim > 1:
		audio = numpy.mean(audio, axis = 1)
	return audio


def cleanse_audio(audio : numpy.ndarray[Any, Any]) -> numpy.ndarray[Any, Any]:
	audio = audio / numpy.max(numpy.abs(audio), axis = 0)
	audio = scipy.signal.resample(audio, len(audio))
	audio = scipy.signal.lfilter([1, -0.97], [1], audio)
	return audio


@lru_cache(maxsize = None)
def create_static_mel_filter(sample_rate : int, filter_total : int, filter_size : int) -> numpy.ndarray[Any, Any]:
	convert_mel_to_hz = lambda x: 700 * (10 ** (x / 2595) - 1)
	convert_hz_to_mel = lambda x: 2595 * numpy.log10(1 + x / 700)
	bins = numpy.linspace(convert_hz_to_mel(55), convert_hz_to_mel(7600), filter_total + 2) # type: ignore
	indices = numpy.floor((filter_size + 1) * convert_mel_to_hz(bins) / sample_rate).astype(numpy.int32) # type: ignore
	filters = numpy.zeros((filter_total, filter_size // 2 + 1))
	for i in range(1, filter_total + 1):
		filters[i - 1, indices[i - 1] : indices[i]] = scipy.signal.windows.triang(indices[i] - indices[i - 1])
	return filters


def create_spectrogram(audio : numpy.ndarray[Any, Any], sample_rate : int, filter_total : int, filter_size : int) -> numpy.ndarray[Any, Any]:
	mel_filters = create_static_mel_filter(sample_rate, filter_total, filter_size)
	spectrogram = scipy.signal.stft(audio, nperseg = filter_size, noverlap = 600, nfft = filter_size)[2]
	spectrogram = numpy.dot(mel_filters, numpy.abs(spectrogram))
	return spectrogram


def extract_spectrogram(spectrogram : numpy.ndarray[Any, Any], filter_total : int, steps : int, fps : float) -> List[numpy.ndarray[Any, Any]]:
	audio_frames = []
	index = 0
	while True:
		start_index = int(index * filter_total / fps)
		if start_index + steps > spectrogram.shape[1]:
			audio_frames.append(spectrogram[:, spectrogram.shape[1] - steps : ])
			break
		audio_frames.append(spectrogram[:, start_index : start_index + steps])
		index += 1
	return audio_frames


@lru_cache(maxsize = None)
def read_static_audio(audio_path : str, fps : Fps) -> List[numpy.ndarray[Any, Any]]:
	buffer = read_audio_buffer(audio_path, 16000, 2)
	audio = numpy.frombuffer(buffer, dtype = numpy.int16).reshape(-1, 2)
	audio = monoize_audio(audio)
	audio = cleanse_audio(audio)
	spectrogram = create_spectrogram(audio, 16000, 80, 800)
	audio_frames = extract_spectrogram(spectrogram, 80, 16, fps)
	return audio_frames


def get_audio_frame(audio_path : str, fps : Fps, frame_number : int) -> Optional[numpy.ndarray[Any, Any]]:
	if audio_path:
		audio_frames = read_static_audio(audio_path, fps)
		if frame_number < len(audio_frames):
			return audio_frames[frame_number]
	return None
