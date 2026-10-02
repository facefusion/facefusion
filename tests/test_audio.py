
import numpy
import pytest
from pytest import approx

from facefusion import ffmpeg, ffmpeg_builder, process_manager, state_manager
from facefusion.audio import convert_hertz_to_mel, convert_mel_to_hertz, count_audio_frame_total, create_empty_audio_frame, create_mel_filter_bank, create_spectrogram, detect_audio_duration, extract_audio_frames, get_audio_frame, prepare_audio, read_static_audio, read_voice, restrict_trim_audio_frame
from facefusion.download import conditional_download
from .assert_helper import get_test_example_file, get_test_examples_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()

	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.mp3'
	])

	ffmpeg.run_ffmpeg(
		ffmpeg_builder.chain(
			ffmpeg_builder.set_input(get_test_example_file('source.mp3')),
			ffmpeg_builder.set_output(get_test_example_file('source.wav'))
		)
	)


def test_get_audio_frame() -> None:
	assert get_audio_frame(get_test_example_file('source.mp3'), 25).shape == (80, 16)
	assert get_audio_frame(get_test_example_file('source.wav'), 25).shape == (80, 16)
	assert get_audio_frame(get_test_example_file('source.mp3'), 25, 279).shape == (80, 16)
	assert get_audio_frame(get_test_example_file('source.mp3'), 25, 280) is None
	assert get_audio_frame(get_test_example_file('source.mp3'), 25, -1) is None
	assert get_audio_frame('invalid', 25) is None


def test_read_static_audio() -> None:
	assert len(read_static_audio(get_test_example_file('source.mp3'), 25)) == 280
	assert len(read_static_audio(get_test_example_file('source.wav'), 25)) == 280
	assert len(read_static_audio(get_test_example_file('source.mp3'), 30)) == 336
	assert len(read_static_audio(get_test_example_file('source.mp3'), 50)) == 560
	assert read_static_audio('invalid', 25) is None


def test_read_voice() -> None:
	assert read_voice(get_test_example_file('invalid.mp3'), 25) is None


def test_extract_audio_frames() -> None:
	spectrogram = numpy.arange(80 * 100).reshape(80, 100)
	audio_frames = extract_audio_frames(spectrogram, 25)

	assert len(audio_frames) == 27
	assert audio_frames[0].shape == (80, 16)
	assert audio_frames[0][0].tolist() == list(range(0, 16))
	assert audio_frames[1][0].tolist() == list(range(3, 19))
	assert audio_frames[2][0].tolist() == list(range(6, 22))
	assert audio_frames[-1][0].tolist() == list(range(83, 99))
	assert len(extract_audio_frames(spectrogram, 50)) == 53
	assert extract_audio_frames(numpy.ones((80, 16)), 25) == []


def test_create_empty_audio_frame() -> None:
	audio_frame = create_empty_audio_frame()

	assert audio_frame.shape == (80, 16)
	assert audio_frame.dtype == numpy.int16
	assert numpy.count_nonzero(audio_frame) == 0


def test_prepare_audio() -> None:
	assert numpy.allclose(prepare_audio(numpy.array([ [ 0, 0 ], [ 2, 4 ], [ -4, -8 ] ])), [ 0.0, 0.5, -1.485 ]) is True
	assert numpy.allclose(prepare_audio(numpy.array([ 0, 4, -8 ])), [ 0.0, 0.5, -1.485 ]) is True


def test_convert_hertz_to_mel() -> None:
	assert convert_hertz_to_mel(0) == 0.0
	assert round(convert_hertz_to_mel(700), 4) == 781.1728
	assert round(convert_hertz_to_mel(1000), 4) == 999.9855


def test_convert_mel_to_hertz() -> None:
	assert convert_mel_to_hertz(numpy.array(0.0)) == 0.0
	assert round(convert_mel_to_hertz(numpy.array(781.1728387480312)).item(), 4) == 700.0
	assert round(convert_mel_to_hertz(convert_hertz_to_mel(1000)).item(), 4) == 1000.0


def test_create_mel_filter_bank() -> None:
	mel_filter_bank = create_mel_filter_bank()

	assert mel_filter_bank.shape == (80, 401)
	assert mel_filter_bank.max() == 1.0
	assert numpy.count_nonzero(mel_filter_bank.sum(axis = 1)) == 80
	assert round(mel_filter_bank.sum(), 4) == 203.0


def test_create_spectrogram() -> None:
	assert create_spectrogram(numpy.zeros(16000)).shape == (80, 81)
	assert create_spectrogram(numpy.zeros(32000)).shape == (80, 161)
	assert numpy.count_nonzero(create_spectrogram(numpy.zeros(16000))) == 0


def test_count_audio_frame_total() -> None:
	assert count_audio_frame_total(get_test_example_file('source.mp3'), 25) == 95
	assert count_audio_frame_total(get_test_example_file('source.mp3'), 30) == 114
	assert count_audio_frame_total(get_test_example_file('source.mp3'), 50) == 190
	assert count_audio_frame_total(get_test_example_file('source.wav'), 25) == 95
	assert count_audio_frame_total('invalid', 25) == 0


def test_detect_audio_duration() -> None:
	assert detect_audio_duration(get_test_example_file('source.mp3')) == approx(3.788, rel = 1e-3)
	assert detect_audio_duration(get_test_example_file('source.wav')) == approx(3.788, rel = 1e-3)
	assert detect_audio_duration('invalid') == 0


def test_restrict_trim_audio_frame() -> None:
	assert restrict_trim_audio_frame(get_test_example_file('source.mp3'), 25, 0, 50) == (0, 50)
	assert restrict_trim_audio_frame(get_test_example_file('source.mp3'), 25, 20, 95) == (20, 95)
	assert restrict_trim_audio_frame(get_test_example_file('source.mp3'), 25, -10, None) == (0, 95)
	assert restrict_trim_audio_frame(get_test_example_file('source.mp3'), 25, None, -10) == (0, 0)
	assert restrict_trim_audio_frame(get_test_example_file('source.mp3'), 25, 100, None) == (95, 95)
	assert restrict_trim_audio_frame(get_test_example_file('source.mp3'), 25, None, 100) == (0, 95)
	assert restrict_trim_audio_frame(get_test_example_file('source.mp3'), 25, None, None) == (0, 95)
