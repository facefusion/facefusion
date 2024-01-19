import subprocess
import pytest

from facefusion.download import conditional_download
from facefusion.vision import get_video_frame, count_video_frame_total, detect_video_fps, detect_video_resolution, pack_resolution, unpack_resolution, create_video_resolutions


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download('.assets/examples',
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-240p.mp4',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-1080p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vf', 'fps=25', '.assets/examples/target-240p-25fps.mp4' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vf', 'fps=30', '.assets/examples/target-240p-30fps.mp4' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vf', 'fps=60', '.assets/examples/target-240p-60fps.mp4' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-240p.mp4', '-vf', 'transpose=0', '.assets/examples/target-240p-90deg.mp4' ])
	subprocess.run([ 'ffmpeg', '-i', '.assets/examples/target-1080p.mp4', '-vf', 'transpose=0', '.assets/examples/target-1080p-90deg.mp4' ])


def test_get_video_frame() -> None:
	assert get_video_frame('.assets/examples/target-240p-25fps.mp4') is not None
	assert get_video_frame('invalid') is None


def test_count_video_frame_total() -> None:
	assert count_video_frame_total('.assets/examples/target-240p-25fps.mp4') == 270
	assert count_video_frame_total('.assets/examples/target-240p-30fps.mp4') == 324
	assert count_video_frame_total('.assets/examples/target-240p-60fps.mp4') == 648
	assert count_video_frame_total('invalid') == 0


def test_detect_video_fps() -> None:
	assert detect_video_fps('.assets/examples/target-240p-25fps.mp4') == 25.0
	assert detect_video_fps('.assets/examples/target-240p-30fps.mp4') == 30.0
	assert detect_video_fps('.assets/examples/target-240p-60fps.mp4') == 60.0
	assert detect_video_fps('invalid') is None


def test_detect_video_resolution() -> None:
	assert detect_video_resolution('.assets/examples/target-240p.mp4') == (426.0, 226.0)
	assert detect_video_resolution('.assets/examples/target-1080p.mp4') == (2048.0, 1080.0)
	assert detect_video_resolution('invalid') is None


def test_pack_resolution() -> None:
	assert pack_resolution((1.0, 1.0)) == '0x0'
	assert pack_resolution((2.0, 2.0)) == '2x2'


def test_unpack_resolution() -> None:
	assert unpack_resolution('0x0') == (0, 0)
	assert unpack_resolution('2x2') == (2, 2)


def test_create_video_resolutions() -> None:
	assert create_video_resolutions('.assets/examples/target-240p.mp4') == [ '426x226', '452x240', '678x360', '904x480', '1018x540', '1358x720', '2036x1080', '2714x1440', '4072x2160' ]
	assert create_video_resolutions('.assets/examples/target-240p-90deg.mp4') == [ '226x426', '240x452', '360x678', '480x904', '540x1018', '720x1358', '1080x2036', '1440x2714', '2160x4072' ]
	assert create_video_resolutions('.assets/examples/target-1080p.mp4') == [ '456x240', '682x360', '910x480', '1024x540', '1366x720', '2048x1080', '2730x1440', '4096x2160' ]
	assert create_video_resolutions('.assets/examples/target-1080p-90deg.mp4') == [ '240x456', '360x682', '480x910', '540x1024', '720x1366', '1080x2048', '1440x2730', '2160x4096' ]
	assert create_video_resolutions('invalid') is None
