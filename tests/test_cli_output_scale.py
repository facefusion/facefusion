import subprocess
import sys
from typing import Optional

import pytest

from facefusion.download import conditional_download
from facefusion.jobs.job_manager import clear_jobs, init_jobs
from facefusion.types import Resolution, Scale
from facefusion.vision import detect_image_resolution, detect_video_resolution
from .helper import get_test_example_file, get_test_examples_directory, get_test_jobs_directory, get_test_output_file, is_test_output_file, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])
	subprocess.run([ 'ffmpeg', '-i', get_test_example_file('target-240p.mp4'), '-vframes', '1', get_test_example_file('target-240p.jpg') ])


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs(get_test_jobs_directory())
	init_jobs(get_test_jobs_directory())
	prepare_test_output_directory()


@pytest.mark.parametrize('scale, expected_resolution, test_name',
[
	(1.0, (426, 226), "original-scale"),
	(0.5, (212, 112), "half-scale"),
	(2.0, (852, 452), "double-scale"),
	(8.0, (3408, 1808), "false-scale"),
])
def test_output_image_scale(scale : Scale, expected_resolution : Optional[Resolution], test_name : str) -> None:
	target_file_path = get_test_example_file('target-240p.jpg')
	output_file_path = get_test_output_file(f'test-{test_name}-on-image.jpg')
	processor = 'face_debugger' if test_name == 'false-scale' else 'frame_enhancer'
	commands = [ sys.executable, 'facefusion.py', 'headless-run', '--jobs-path', get_test_jobs_directory(), '--processors', processor, '-t', target_file_path, '-o', output_file_path, '--output-image-scale', str(scale) ]

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file(f'test-{test_name}-on-image.jpg') is True
	assert detect_image_resolution(output_file_path) == expected_resolution


@pytest.mark.parametrize('scale, expected_resolution, test_name',
[
	(1.0, (426, 226), 'original-scale'),
	(0.5, (212, 112), 'half-scale'),
	(2.0, (852, 452), 'double-scale'),
	(8.0, (3408, 1808), 'false-scale'),
])
def test_output_video_scale(scale : Scale, expected_resolution : Optional[Resolution], test_name : str) -> None:
	target_file_path = get_test_example_file('target-240p.mp4')
	output_file_path = get_test_output_file(f'test-{test_name}-on-video.mp4')
	processor = 'face_debugger' if test_name == 'false-scale' else 'frame_enhancer'
	commands = [ sys.executable, 'facefusion.py', 'headless-run', '--jobs-path', get_test_jobs_directory(), '--processors', processor, '-t', target_file_path, '-o', output_file_path, '--trim-frame-end', '1' ]

	if scale:
		commands.extend(['--output-video-scale', str(scale)])

	assert subprocess.run(commands).returncode == 0
	assert is_test_output_file(f'test-{test_name}-on-video.mp4') is True
	assert detect_video_resolution(output_file_path) == expected_resolution
