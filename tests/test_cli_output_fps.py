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

	for output_video_fps in [ 30, 60 ]:
		ffmpeg.run_ffmpeg(
			ffmpeg_builder.chain(
				ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
				ffmpeg_builder.select_frame_range(0, 30, output_video_fps),
				ffmpeg_builder.set_video_encoder('libx264'),
				ffmpeg_builder.enforce_pixel_format('yuv420p'),
				[
					'-crf',
					'0',
					'-an'
				],
				ffmpeg_builder.force_output(get_test_example_file('target-240p-30frames-' + str(output_video_fps) + 'fps.mp4'))
			)
		)


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs(get_test_jobs_directory())
	init_jobs(get_test_jobs_directory())
	prepare_test_output_directory()


@pytest.mark.parametrize('workflow_strategy, output_video_fps, trim_frame_end, output_video_frame_total',
[
	('disk', 30, 30, 36),
	('memory', 30, 30, 36),
	('disk', 60, 30, 72),
	('memory', 60, 30, 72)
])
def test_output_video_fps(workflow_strategy : WorkflowStrategy, output_video_fps : Fps, trim_frame_end : int, output_video_frame_total : int) -> None:
	actual_file_path = get_test_output_file('test-output-video-fps-actual-' + workflow_strategy + '-' + str(output_video_fps) + '.mp4')
	expect_file_path = get_test_output_file('test-output-video-fps-expect-' + workflow_strategy + '-' + str(output_video_fps) + '.mp4')
	actual_commands = [ sys.executable, 'facefusion.py', 'headless-run', '--jobs-path', get_test_jobs_directory(), '--workflow-strategy', workflow_strategy, '-s', get_test_example_file('source.jpg'), '-t', get_test_example_file('target-240p.mp4'), '-o', actual_file_path, '--trim-frame-end', str(trim_frame_end), '--output-video-fps', str(output_video_fps) ]
	expect_commands = [ sys.executable, 'facefusion.py', 'headless-run', '--jobs-path', get_test_jobs_directory(), '--workflow-strategy', workflow_strategy, '-s', get_test_example_file('source.jpg'), '-t', get_test_example_file('target-240p-30frames-' + str(output_video_fps) + 'fps.mp4'), '-o', expect_file_path ]

	assert subprocess.run(actual_commands).returncode == 0
	assert subprocess.run(expect_commands).returncode == 0

	assert detect_video_fps(actual_file_path) == output_video_fps
	assert count_video_frame_total(actual_file_path) == output_video_frame_total
	assert count_video_frame_total(expect_file_path) == output_video_frame_total

	for frame_number in range(output_video_frame_total):
		actual_vision_frame = read_video_frame(actual_file_path, frame_number)
		expect_vision_frame = read_video_frame(expect_file_path, frame_number)

		assert numpy.array_equal(actual_vision_frame, expect_vision_frame) is True
