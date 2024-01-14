import subprocess
import pytest

from facefusion.download import conditional_download
from facefusion.vision import get_video_frame, detect_video_fps, detect_video_resolution, count_video_frame_total


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


def test_get_video_frame() -> None:
	assert get_video_frame('.assets/examples/target-240p-25fps.mp4') is not None
	assert get_video_frame('invalid') is None


def test_detect_video_fps() -> None:
	assert detect_video_fps('.assets/examples/target-240p-25fps.mp4') == 25.0
	assert detect_video_fps('.assets/examples/target-240p-30fps.mp4') == 30.0
	assert detect_video_fps('.assets/examples/target-240p-60fps.mp4') == 60.0
	assert detect_video_fps('invalid') is None


def test_detect_video_resolution() -> None:
	assert detect_video_resolution('.assets/examples/target-240p.mp4') == (426.0, 226.0)
	assert detect_video_resolution('.assets/examples/target-1080p.mp4') == (2048.0, 1080.0)
	assert detect_video_resolution('invalid') is None


def test_count_video_frame_total() -> None:
	assert count_video_frame_total('.assets/examples/target-240p-25fps.mp4') == 270
	assert count_video_frame_total('.assets/examples/target-240p-30fps.mp4') == 324
	assert count_video_frame_total('.assets/examples/target-240p-60fps.mp4') == 648
	assert count_video_frame_total('invalid') == 0
