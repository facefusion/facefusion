from typing import Optional, Any, List

import numpy
import scipy
from functools import lru_cache
from facefusion.ffmpeg import read_audio_buffer
from facefusion.typing import Fps, Audio, Spectrogram, AudioFrame


def get_audio_frame(audio_path : str, fps : Fps, frame_number : int) -> Optional[AudioFrame]:
	if audio_path:
		audio_frames = read_static_audio(audio_path, fps)
		if frame_number < len(audio_frames):
			return audio_frames[frame_number]
	return None


@lru_cache(maxsize = None)
def read_static_audio(audio_path : str, fps : Fps) -> List[Optional[AudioFrame]]:
	audio_buffer = read_audio_buffer(audio_path, 16000, 2)
	audio = numpy.frombuffer(audio_buffer, dtype = numpy.int16).reshape(-1, 2)
	audio = normalize_audio(audio)
	spectrogram = create_spectrogram(audio, 16000, 80, 800)
	audio_frames = extract_audio_frames(spectrogram, 80, 16, fps)
	return audio_frames


def normalize_audio(audio : numpy.ndarray[Any, Any]) -> Audio:
	if audio.ndim > 1:
		audio = numpy.mean(audio, axis = 1)
	audio = audio / numpy.max(numpy.abs(audio), axis = 0)
	audio = scipy.signal.resample(audio, len(audio))
	audio = scipy.signal.lfilter([1, -0.97], [1], audio)
	return audio


@lru_cache(maxsize = None)
def create_static_mel_filter(sample_rate : int, filter_total : int, filter_size : int) -> numpy.ndarray[Any, Any]:
	bins = (10 ** (numpy.linspace(85, 2787, filter_total + 2) / 2595) - 1) * 700
	indices = numpy.floor((filter_size + 1) * bins / sample_rate).astype(numpy.int16)
	filters = numpy.zeros((filter_total, filter_size // 2 + 1))
	for index in range(1, filter_total + 1):
		filters[index - 1, indices[index - 1] : indices[index]] = scipy.signal.windows.triang(indices[index] - indices[index - 1])
	return filters


def create_spectrogram(audio : Audio, sample_rate : int, filter_total : int, filter_size : int) -> Spectrogram:
	mel_filters = create_static_mel_filter(sample_rate, filter_total, filter_size)
	spectrogram = scipy.signal.stft(audio, nperseg = filter_size, noverlap = 600, nfft = filter_size)[2]
	spectrogram = numpy.dot(mel_filters, numpy.abs(spectrogram))
	return spectrogram


def extract_audio_frames(spectrogram : Spectrogram, filter_total : int, steps : int, fps : Fps) -> List[Optional[AudioFrame]]:
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
