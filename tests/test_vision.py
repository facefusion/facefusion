import subprocess

import pytest

from facefusion.download import conditional_download
from facefusion.vision import calc_histogram_difference, count_trim_frame_total, count_video_frame_total, create_image_resolutions, create_video_resolutions, detect_image_resolution, detect_video_duration, detect_video_fps, detect_video_resolution, match_frame_color, normalize_resolution, pack_resolution, predict_video_frame_total, read_image, read_video_frame, restrict_image_resolution, restrict_trim_frame, restrict_video_fps, restrict_video_resolution, unpack_resolution, write_image
from .helper import get_test_example_file, get_test_examples_directory, get_test_output_file, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-1080p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vframes', '1', get_test_example_file('target-240p.jpg') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vframes', '1', get_test_example_file('目标-240p.webp') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-1080p.mp4'), '-vframes', '1', get_test_example_file('target-1080p.jpg') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vframes', '1', '-vf', 'hue=s=0', get_test_example_file('target-240p-0sat.jpg') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vframes', '1', '-vf', 'transpose=0', get_test_example_file('target-240p-90deg.jpg') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-1080p.mp4'), '-vframes', '1', '-vf', 'transpose=0', get_test_example_file('target-1080p-90deg.jpg') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vf', 'fps=25', get_test_example_file('target-240p-25fps.mp4') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vf', 'fps=30', get_test_example_file('target-240p-30fps.mp4') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vf', 'fps=60', get_test_example_file('target-240p-60fps.mp4') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vf', 'transpose=0', get_test_example_file('target-240p-90deg.mp4') ])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-1080p.mp4'), '-vf', 'transpose=0', get_test_example_file('target-1080p-90deg.mp4') ])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	prepare_test_output_directory()


def test_read_image() -> None:
	assert read_image(get_test_example_file('target-240p.jpg')).shape == (226, 426, 3)
	assert read_image(get_test_example_file('目标-240p.webp')).shape == (226, 426, 3)
	assert read_image('invalid') is None


def test_write_image() -> None:
	vision_frame = read_image(get_test_example_file('target-240p.jpg'))

	assert write_image(get_test_output_file('target-240p.jpg'), vision_frame) is True
	assert write_image(get_test_output_file('目标-240p.webp'), vision_frame) is True


def test_detect_image_resolution() -> None:
	assert detect_image_resolution(get_test_example_file('target-240p.jpg')) == (426, 226)
	assert detect_image_resolution(get_test_example_file('target-240p-90deg.jpg')) == (226, 426)
	assert detect_image_resolution(get_test_example_file('target-1080p.jpg')) == (2048, 1080)
	assert detect_image_resolution(get_test_example_file('target-1080p-90deg.jpg')) == (1080, 2048)
	assert detect_image_resolution('invalid') is None


def test_restrict_image_resolution() -> None:
	assert restrict_image_resolution(get_test_example_file('target-1080p.jpg'), (426, 226)) == (426, 226)
	assert restrict_image_resolution(get_test_example_file('target-1080p.jpg'), (2048, 1080)) == (2048, 1080)
	assert restrict_image_resolution(get_test_example_file('target-1080p.jpg'), (4096, 2160)) == (2048, 1080)


def test_create_image_resolutions() -> None:
	assert create_image_resolutions((426, 226)) == [ '106x56', '212x112', '320x170', '426x226', '640x340', '852x452', '1064x564', '1278x678', '1492x792', '1704x904' ]
	assert create_image_resolutions((226, 426)) == [ '56x106', '112x212', '170x320', '226x426', '340x640', '452x852', '564x1064', '678x1278', '792x1492', '904x1704' ]
	assert create_image_resolutions((2048, 1080)) == [ '512x270', '1024x540', '1536x810', '2048x1080', '3072x1620', '4096x2160', '5120x2700', '6144x3240', '7168x3780', '8192x4320' ]
	assert create_image_resolutions((1080, 2048)) == [ '270x512', '540x1024', '810x1536', '1080x2048', '1620x3072', '2160x4096', '2700x5120', '3240x6144', '3780x7168', '4320x8192' ]
	assert create_image_resolutions(None) == []


def test_read_video_frame() -> None:
	assert hasattr(read_video_frame(get_test_example_file('target-240p-25fps.mp4')), '__array_interface__')
	assert read_video_frame('invalid') is None


def test_count_video_frame_total() -> None:
	assert count_video_frame_total(get_test_example_file('target-240p-25fps.mp4')) == 270
	assert count_video_frame_total(get_test_example_file('target-240p-30fps.mp4')) == 324
	assert count_video_frame_total(get_test_example_file('target-240p-60fps.mp4')) == 648
	assert count_video_frame_total('invalid') == 0


def test_predict_video_frame_total() -> None:
	assert predict_video_frame_total(get_test_example_file('target-240p-25fps.mp4'), 12.5, 0, 100) == 50
	assert predict_video_frame_total(get_test_example_file('target-240p-25fps.mp4'), 25, 0, 100) == 100
	assert predict_video_frame_total(get_test_example_file('target-240p-25fps.mp4'), 25, 0, 200) == 200
	assert predict_video_frame_total('invalid', 25, 0, 100) == 0


def test_detect_video_fps() -> None:
	assert detect_video_fps(get_test_example_file('target-240p-25fps.mp4')) == 25.0
	assert detect_video_fps(get_test_example_file('target-240p-30fps.mp4')) == 30.0
	assert detect_video_fps(get_test_example_file('target-240p-60fps.mp4')) == 60.0
	assert detect_video_fps('invalid') is None


def test_restrict_video_fps() -> None:
	assert restrict_video_fps(get_test_example_file('target-1080p.mp4'), 20.0) == 20.0
	assert restrict_video_fps(get_test_example_file('target-1080p.mp4'), 25.0) == 25.0
	assert restrict_video_fps(get_test_example_file('target-1080p.mp4'), 60.0) == 25.0


def test_detect_video_duration() -> None:
	assert detect_video_duration(get_test_example_file('target-240p.mp4')) == 10.8
	assert detect_video_duration('invalid') == 0


def test_count_trim_frame_total() -> None:
	assert count_trim_frame_total(get_test_example_file('target-240p.mp4'), 0, 200) == 200
	assert count_trim_frame_total(get_test_example_file('target-240p.mp4'), 70, 270) == 200
	assert count_trim_frame_total(get_test_example_file('target-240p.mp4'), -10, None) == 270
	assert count_trim_frame_total(get_test_example_file('target-240p.mp4'), None, -10) == 0
	assert count_trim_frame_total(get_test_example_file('target-240p.mp4'), 280, None) == 0
	assert count_trim_frame_total(get_test_example_file('target-240p.mp4'), None, 280) == 270
	assert count_trim_frame_total(get_test_example_file('target-240p.mp4'), None, None) == 270


def test_restrict_trim_frame() -> None:
	assert restrict_trim_frame(get_test_example_file('target-240p.mp4'), 0, 200) == (0, 200)
	assert restrict_trim_frame(get_test_example_file('target-240p.mp4'), 70, 270) == (70, 270)
	assert restrict_trim_frame(get_test_example_file('target-240p.mp4'), -10, None) == (0, 270)
	assert restrict_trim_frame(get_test_example_file('target-240p.mp4'), None, -10) == (0, 0)
	assert restrict_trim_frame(get_test_example_file('target-240p.mp4'), 280, None) == (270, 270)
	assert restrict_trim_frame(get_test_example_file('target-240p.mp4'), None, 280) == (0, 270)
	assert restrict_trim_frame(get_test_example_file('target-240p.mp4'), None, None) == (0, 270)


def test_detect_video_resolution() -> None:
	assert detect_video_resolution(get_test_example_file('target-240p.mp4')) == (426, 226)
	assert detect_video_resolution(get_test_example_file('target-240p-90deg.mp4')) == (226, 426)
	assert detect_video_resolution(get_test_example_file('target-1080p.mp4')) == (2048, 1080)
	assert detect_video_resolution(get_test_example_file('target-1080p-90deg.mp4')) == (1080, 2048)
	assert detect_video_resolution('invalid') is None


def test_restrict_video_resolution() -> None:
	assert restrict_video_resolution(get_test_example_file('target-1080p.mp4'), (426, 226)) == (426, 226)
	assert restrict_video_resolution(get_test_example_file('target-1080p.mp4'), (2048, 1080)) == (2048, 1080)
	assert restrict_video_resolution(get_test_example_file('target-1080p.mp4'), (4096, 2160)) == (2048, 1080)


def test_create_video_resolutions() -> None:
	assert create_video_resolutions((426, 226)) == [ '426x226', '452x240', '678x360', '904x480', '1018x540', '1358x720', '2036x1080', '2714x1440', '4072x2160', '8144x4320' ]
	assert create_video_resolutions((226, 426)) == [ '226x426', '240x452', '360x678', '480x904', '540x1018', '720x1358', '1080x2036', '1440x2714', '2160x4072', '4320x8144' ]
	assert create_video_resolutions((2048, 1080)) == [ '456x240', '682x360', '910x480', '1024x540', '1366x720', '2048x1080', '2730x1440', '4096x2160', '8192x4320' ]
	assert create_video_resolutions((1080, 2048)) == [ '240x456', '360x682', '480x910', '540x1024', '720x1366', '1080x2048', '1440x2730', '2160x4096', '4320x8192' ]
	assert create_video_resolutions(None) == []


def test_normalize_resolution() -> None:
	assert normalize_resolution((2.5, 2.5)) == (2, 2)
	assert normalize_resolution((3.0, 3.0)) == (4, 4)
	assert normalize_resolution((6.5, 6.5)) == (6, 6)


def test_pack_resolution() -> None:
	assert pack_resolution((1, 1)) == '0x0'
	assert pack_resolution((2, 2)) == '2x2'


def test_unpack_resolution() -> None:
	assert unpack_resolution('0x0') == (0, 0)
	assert unpack_resolution('2x2') == (2, 2)


def test_calc_histogram_difference() -> None:
	source_vision_frame = read_image(get_test_example_file('target-240p.jpg'))
	target_vision_frame = read_image(get_test_example_file('target-240p-0sat.jpg'))

	assert calc_histogram_difference(source_vision_frame, source_vision_frame) == 1.0
	assert calc_histogram_difference(source_vision_frame, target_vision_frame) < 0.5


def test_match_frame_color() -> None:
	source_vision_frame = read_image(get_test_example_file('target-240p.jpg'))
	target_vision_frame = read_image(get_test_example_file('target-240p-0sat.jpg'))
	output_vision_frame = match_frame_color(source_vision_frame, target_vision_frame)

	assert calc_histogram_difference(source_vision_frame, output_vision_frame) > 0.5
