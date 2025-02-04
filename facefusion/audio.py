from typing import Optional, Any, List
from functools import lru_cache
import numpy
import scipy

from facefusion.filesystem import is_audio
from facefusion.ffmpeg import read_audio_buffer
from facefusion.typing import Fps, Audio, AudioFrame, Spectrogram, MelFilterBank
from facefusion.voice_extractor import batch_extract_voice


@lru_cache(maxsize = 128)
def read_static_audio(audio_path : str, fps : Fps) -> Optional[List[AudioFrame]]:
	return read_audio(audio_path, fps)


def read_audio(audio_path : str, fps : Fps) -> Optional[List[AudioFrame]]:
	sample_rate = 48000
	channel_total = 2

	if is_audio(audio_path):
		audio_buffer = read_audio_buffer(audio_path, sample_rate, channel_total)
		audio = numpy.frombuffer(audio_buffer, dtype = numpy.int16).reshape(-1, 2)
		audio = prepare_audio(audio)
		spectrogram = create_spectrogram(audio)
		audio_frames = extract_audio_frames(spectrogram, fps)
		return audio_frames
	return None


@lru_cache(maxsize = 128)
def read_static_voice(audio_path : str, fps : Fps) -> Optional[List[AudioFrame]]:
	return read_voice(audio_path, fps)


def read_voice(audio_path : str, fps : Fps) -> Optional[List[AudioFrame]]:
	sample_rate = 48000
	channel_total = 2
	chunk_size = 1024 * 240
	step_size = 1024 * 180

	if is_audio(audio_path):
		audio_buffer = read_audio_buffer(audio_path, sample_rate, channel_total)
		audio = numpy.frombuffer(audio_buffer, dtype = numpy.int16).reshape(-1, 2)
		audio = batch_extract_voice(audio, chunk_size, step_size)
		audio = prepare_voice(audio)
		spectrogram = create_spectrogram(audio)
		audio_frames = extract_audio_frames(spectrogram, fps)
		return audio_frames
	return None


def get_audio_frame(audio_path : str, fps : Fps, frame_number : int = 0) -> Optional[AudioFrame]:
	if is_audio(audio_path):
		audio_frames = read_static_audio(audio_path, fps)
		if frame_number in range(len(audio_frames)):
			return audio_frames[frame_number]
	return None


def get_voice_frame(audio_path : str, fps : Fps, frame_number : int = 0) -> Optional[AudioFrame]:
	if is_audio(audio_path):
		voice_frames = read_static_voice(audio_path, fps)
		if frame_number in range(len(voice_frames)):
			return voice_frames[frame_number]
	return None


def create_empty_audio_frame() -> AudioFrame:
	mel_filter_total = 80
	step_size = 16
	audio_frame = numpy.zeros((mel_filter_total, step_size)).astype(numpy.int16)
	return audio_frame


def prepare_audio(audio : numpy.ndarray[Any, Any]) -> Audio:
	if audio.ndim > 1:
		audio = numpy.mean(audio, axis = 1)
	audio = audio / numpy.max(numpy.abs(audio), axis = 0)
	audio = scipy.signal.lfilter([ 1.0, -0.97 ], [ 1.0 ], audio)
	return audio


def prepare_voice(audio : numpy.ndarray[Any, Any]) -> Audio:
	sample_rate = 48000
	resample_rate = 16000

	audio = scipy.signal.resample(audio, int(len(audio) * resample_rate / sample_rate))
	audio = prepare_audio(audio)
	return audio


def convert_hertz_to_mel(hertz : float) -> float:
	return 2595 * numpy.log10(1 + hertz / 700)


def convert_mel_to_hertz(mel : numpy.ndarray[Any, Any]) -> numpy.ndarray[Any, Any]:
	return 700 * (10 ** (mel / 2595) - 1)


def create_mel_filter_bank() -> MelFilterBank:
	mel_filter_total = 80
	mel_bin_total = 800
	sample_rate = 16000
	min_frequency = 55.0
	max_frequency = 7600.0
	mel_filter_bank = numpy.zeros((mel_filter_total, mel_bin_total // 2 + 1))
	mel_frequency_range = numpy.linspace(convert_hertz_to_mel(min_frequency), convert_hertz_to_mel(max_frequency), mel_filter_total + 2)
	indices = numpy.floor((mel_bin_total + 1) * convert_mel_to_hertz(mel_frequency_range) / sample_rate).astype(numpy.int16)

	for index in range(mel_filter_total):
		start = indices[index]
		end = indices[index + 1]
		mel_filter_bank[index, start:end] = scipy.signal.windows.triang(end - start)
	return mel_filter_bank


def create_spectrogram(audio : Audio) -> Spectrogram:
	mel_bin_total = 800
	mel_bin_overlap = 600
	mel_filter_bank = create_mel_filter_bank()
	spectrogram = scipy.signal.stft(audio, nperseg = mel_bin_total, nfft = mel_bin_total, noverlap = mel_bin_overlap)[2]
	spectrogram = numpy.dot(mel_filter_bank, numpy.abs(spectrogram))
	return spectrogram


def extract_audio_frames(spectrogram : Spectrogram, fps : Fps) -> List[AudioFrame]:
	mel_filter_total = 80
	step_size = 16
	audio_frames = []
	indices = numpy.arange(0, spectrogram.shape[1], mel_filter_total / fps).astype(numpy.int16)
	indices = indices[indices >= step_size]

	for index in indices:
		start = max(0, index - step_size)
		audio_frames.append(spectrogram[:, start:index])
	return audio_frames
