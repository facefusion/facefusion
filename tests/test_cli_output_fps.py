import subprocess
import sys

import numpy
import pytest

from facefusion import ffmpeg, ffmpeg_builder, process_manager
from facefusion.download import conditional_download
from facefusion.jobs.job_manager import clear_jobs, init_jobs
from facefusion.types import Fps, WorkflowStrategy
from facefusion.vision import count_video_frame_total, detect_video_fps, read_video_frame
from .helper import get_test_example_file, get_test_examples_directory, get_test_jobs_directory, get_test_output_file, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])

	ffmpeg.run_ffmpeg(
		ffmpeg_builder.chain(
			ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
			ffmpeg_builder.select_frame_range(0, 40, 6.25),
			ffmpeg_builder.set_video_encoder('libx264'),
			ffmpeg_builder.enforce_pixel_format('yuv420p'),
			[
				'-crf',
				'0',
				'-an'
			],
			ffmpeg_builder.force_output(get_test_example_file('target-240p-6.25fps.mp4'))
		)
	)


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs(get_test_jobs_directory())
	init_jobs(get_test_jobs_directory())
	prepare_test_output_directory()


@pytest.mark.parametrize('workflow_strategy, output_video_fps, output_video_frame_total',
[
	('disk', 6.25, 10),
	('memory', 6.25, 10)
])
def test_output_video_fps(workflow_strategy : WorkflowStrategy, output_video_fps : Fps, output_video_frame_total : int) -> None:
	output_file_path = get_test_output_file('test-output-video-fps-' + workflow_strategy + '-' + str(output_video_fps) + '.mp4')
	resample_file_path = get_test_output_file('test-output-video-fps-resample-' + workflow_strategy + '-' + str(output_video_fps) + '.mp4')
	commands = [ sys.executable, 'facefusion.py', 'headless-run', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_swapper', '--execution-providers', 'cpu', '-s', get_test_example_file('source.jpg'), '-t', get_test_example_file('target-240p.mp4'), '-o', output_file_path, '--trim-frame-end', '40', '--workflow-strategy', workflow_strategy, '--output-video-fps', str(output_video_fps) ]
	resample_commands = [ sys.executable, 'facefusion.py', 'headless-run', '--jobs-path', get_test_jobs_directory(), '--processors', 'face_swapper', '--execution-providers', 'cpu', '-s', get_test_example_file('source.jpg'), '-t', get_test_example_file('target-240p-' + str(output_video_fps) + 'fps.mp4'), '-o', resample_file_path, '--workflow-strategy', workflow_strategy ]

	assert subprocess.run(commands).returncode == 0
	assert subprocess.run(resample_commands).returncode == 0
	assert detect_video_fps(output_file_path) == output_video_fps
	assert count_video_frame_total(output_file_path) == output_video_frame_total
	assert count_video_frame_total(resample_file_path) == output_video_frame_total

	for frame_number in range(output_video_frame_total):
		assert numpy.array_equal(read_video_frame(output_file_path, frame_number), read_video_frame(resample_file_path, frame_number)) is True
