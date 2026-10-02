import os
from time import sleep

import pytest

from facefusion import ffmpeg, ffmpeg_builder, process_manager, state_manager
from facefusion.download import conditional_download
from facefusion.ffprobe import extract_video_metadata
from facefusion.filesystem import copy_file, create_directory, get_file_extension, is_directory, resolve_file_paths
from facefusion.jobs.job_manager import add_step, clear_jobs, create_job, get_steps, init_jobs, move_job_file, submit_job, submit_jobs
from facefusion.jobs.job_runner import clean_steps, collect_output_set, finalize_steps, retry_job, retry_jobs, run_job, run_jobs, run_step, run_steps
from facefusion.types import Args
from .assert_helper import get_test_example_file, get_test_examples_directory, get_test_jobs_directory, get_test_output_path, is_test_job_file, is_test_output_file, is_test_output_sequence, prepare_test_output_directory


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init()
	state_manager.init_item('jobs_path', get_test_jobs_directory())

	process_manager.start()
	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4'
	])

	ffmpeg.run_ffmpeg(
		ffmpeg_builder.chain(
			ffmpeg_builder.set_input(get_test_example_file('target-240p.mp4')),
			[
				'-vframes',
				'1'
			],
			ffmpeg_builder.set_output(get_test_example_file('target-240p.jpg'))
		)
	)


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	clear_jobs(get_test_jobs_directory())
	init_jobs(state_manager.get_jobs_path())
	prepare_test_output_directory()


def process_step(job_id : str, step_index : int, step_args : Args) -> bool:
	output_path = step_args.get('output_path')
	target_path = step_args.get('target_path')

	if output_path and not get_file_extension(output_path):
		if create_directory(output_path):
			return copy_file(target_path, os.path.join(output_path, os.path.basename(target_path)))
		return False

	return copy_file(target_path, output_path)


def test_run_job() -> None:
	args_1 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_path('output-1.mp4')
	}
	args_2 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_path('output-2.mp4')
	}
	args_3 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_path('output-3.jpg')
	}
	args_4 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_path('output-4')
	}
	args_5 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_path('output-4')
	}

	assert run_job('job-invalid', process_step) is False

	create_job('job-test-run-job')
	add_step('job-test-run-job', args_1)
	add_step('job-test-run-job', args_2)
	add_step('job-test-run-job', args_2)
	add_step('job-test-run-job', args_3)
	add_step('job-test-run-job', args_4)
	add_step('job-test-run-job', args_5)

	assert run_job('job-test-run-job', process_step) is False

	submit_job('job-test-run-job')

	assert run_job('job-test-run-job', process_step) is True
	assert is_test_job_file('job-test-run-job.json', 'queued') is False
	assert is_test_job_file('job-test-run-job.json', 'completed') is True
	assert get_steps('job-test-run-job')[0].get('status') == 'completed'
	assert get_steps('job-test-run-job')[3].get('status') == 'completed'
	assert get_steps('job-test-run-job')[5].get('status') == 'completed'
	assert extract_video_metadata(get_test_output_path('output-1.mp4')).get('frame_total') == 270
	assert extract_video_metadata(get_test_output_path('output-2.mp4')).get('frame_total') == 540
	assert is_test_output_file('output-3.jpg') is True
	assert is_test_output_sequence(get_test_output_path('output-4')) is True
	assert is_test_output_file('output-1-job-test-run-job-0.mp4') is False
	assert is_test_output_file('output-2-job-test-run-job-1.mp4') is False
	assert is_test_output_file('output-2-job-test-run-job-2.mp4') is False
	assert is_test_output_file('output-3-job-test-run-job-3.jpg') is False
	assert is_directory(get_test_output_path('output-4-job-test-run-job-4')) is False
	assert is_directory(get_test_output_path('output-4-job-test-run-job-5')) is False
	assert run_job('job-test-run-job', process_step) is False

	args_6 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': 'invalid',
		'output_path': get_test_output_path('output-6.mp4')
	}

	create_job('job-test-run-job-failed')
	add_step('job-test-run-job-failed', args_1)
	add_step('job-test-run-job-failed', args_6)
	add_step('job-test-run-job-failed', args_1)
	submit_job('job-test-run-job-failed')

	assert run_job('job-test-run-job-failed', process_step) is False
	assert is_test_job_file('job-test-run-job-failed.json', 'queued') is False
	assert is_test_job_file('job-test-run-job-failed.json', 'failed') is True
	assert get_steps('job-test-run-job-failed')[0].get('status') == 'completed'
	assert get_steps('job-test-run-job-failed')[1].get('status') == 'failed'
	assert get_steps('job-test-run-job-failed')[2].get('status') == 'queued'
	assert is_test_output_file('output-1-job-test-run-job-failed-0.mp4') is False
	assert is_test_output_file('output-6.mp4') is False


def test_run_jobs() -> None:
	args_1 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_path('output-1.mp4')
	}
	args_2 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_path('output-2.mp4')
	}
	args_3 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_path('output-3.jpg')
	}
	halt_on_error = True

	assert run_jobs(process_step, halt_on_error) is False

	create_job('job-test-run-jobs-1')
	create_job('job-test-run-jobs-2')
	add_step('job-test-run-jobs-1', args_1)
	add_step('job-test-run-jobs-1', args_1)
	add_step('job-test-run-jobs-2', args_2)
	add_step('job-test-run-jobs-3', args_3)

	assert run_jobs(process_step, halt_on_error) is False

	submit_jobs(halt_on_error)

	assert run_jobs(process_step, halt_on_error) is True
	assert is_test_job_file('job-test-run-jobs-1.json', 'completed') is True
	assert is_test_job_file('job-test-run-jobs-2.json', 'completed') is True
	assert run_jobs(process_step, halt_on_error) is False

	args_4 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': 'invalid',
		'output_path': get_test_output_path('output-4.mp4')
	}

	create_job('job-test-run-jobs-4')
	add_step('job-test-run-jobs-4', args_4)
	submit_job('job-test-run-jobs-4')
	sleep(0.5)
	create_job('job-test-run-jobs-5')
	add_step('job-test-run-jobs-5', args_2)
	submit_job('job-test-run-jobs-5')

	assert run_jobs(process_step, halt_on_error) is False
	assert is_test_job_file('job-test-run-jobs-4.json', 'failed') is True
	assert is_test_job_file('job-test-run-jobs-5.json', 'queued') is True

	halt_on_error = False
	move_job_file('job-test-run-jobs-4', 'queued')

	assert run_jobs(process_step, halt_on_error) is False
	assert is_test_job_file('job-test-run-jobs-4.json', 'failed') is True
	assert is_test_job_file('job-test-run-jobs-5.json', 'completed') is True


def test_retry_job() -> None:
	args_1 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_path('output-1.mp4')
	}

	assert retry_job('job-invalid', process_step) is False

	create_job('job-test-retry-job')
	add_step('job-test-retry-job', args_1)
	submit_job('job-test-retry-job')

	assert retry_job('job-test-retry-job', process_step) is False

	move_job_file('job-test-retry-job', 'failed')

	assert retry_job('job-test-retry-job', process_step) is True
	assert is_test_job_file('job-test-retry-job.json', 'completed') is True
	assert get_steps('job-test-retry-job')[0].get('status') == 'completed'
	assert retry_job('job-test-retry-job', process_step) is False

	args_2 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': 'invalid',
		'output_path': get_test_output_path('output-2.mp4')
	}

	create_job('job-test-retry-job-failed')
	add_step('job-test-retry-job-failed', args_2)
	add_step('job-test-retry-job-failed', args_1)
	submit_job('job-test-retry-job-failed')
	move_job_file('job-test-retry-job-failed', 'failed')

	assert retry_job('job-test-retry-job-failed', process_step) is False
	assert is_test_job_file('job-test-retry-job-failed.json', 'failed') is True
	assert get_steps('job-test-retry-job-failed')[0].get('status') == 'failed'
	assert get_steps('job-test-retry-job-failed')[1].get('status') == 'queued'


def test_retry_jobs() -> None:
	args_1 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_path('output-1.mp4')
	}
	args_2 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_path('output-2.mp4')
	}
	args_3 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_path('output-3.jpg')
	}
	halt_on_error = True

	assert retry_jobs(process_step, halt_on_error) is False

	create_job('job-test-retry-jobs-1')
	create_job('job-test-retry-jobs-2')
	add_step('job-test-retry-jobs-1', args_1)
	add_step('job-test-retry-jobs-1', args_1)
	add_step('job-test-retry-jobs-2', args_2)
	add_step('job-test-retry-jobs-3', args_3)

	assert retry_jobs(process_step, halt_on_error) is False

	move_job_file('job-test-retry-jobs-1', 'failed')
	move_job_file('job-test-retry-jobs-2', 'failed')

	assert retry_jobs(process_step, halt_on_error) is True
	assert is_test_job_file('job-test-retry-jobs-1.json', 'completed') is True
	assert is_test_job_file('job-test-retry-jobs-2.json', 'completed') is True
	assert retry_jobs(process_step, halt_on_error) is False

	args_4 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': 'invalid',
		'output_path': get_test_output_path('output-4.mp4')
	}

	create_job('job-test-retry-jobs-4')
	add_step('job-test-retry-jobs-4', args_4)
	move_job_file('job-test-retry-jobs-4', 'failed')
	sleep(0.5)
	create_job('job-test-retry-jobs-5')
	add_step('job-test-retry-jobs-5', args_2)
	move_job_file('job-test-retry-jobs-5', 'failed')

	assert retry_jobs(process_step, halt_on_error) is False
	assert is_test_job_file('job-test-retry-jobs-4.json', 'failed') is True
	assert is_test_job_file('job-test-retry-jobs-5.json', 'failed') is True

	halt_on_error = False

	assert retry_jobs(process_step, halt_on_error) is False
	assert is_test_job_file('job-test-retry-jobs-4.json', 'failed') is True
	assert is_test_job_file('job-test-retry-jobs-5.json', 'completed') is True


def test_run_step() -> None:
	args_1 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_path('output-1.mp4')
	}
	args_2 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': 'invalid',
		'output_path': get_test_output_path('output-2.mp4')
	}
	args_3 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_path('output-3')
	}

	create_job('job-test-run-step')
	add_step('job-test-run-step', args_1)
	add_step('job-test-run-step', args_2)
	add_step('job-test-run-step', args_3)
	steps = get_steps('job-test-run-step')

	assert run_step('job-test-run-step', 0, steps[0], process_step) is True
	assert get_steps('job-test-run-step')[0].get('status') == 'completed'
	assert get_steps('job-test-run-step')[1].get('status') == 'drafted'
	assert is_test_output_file('output-1.mp4') is False
	assert is_test_output_file('output-1-job-test-run-step-0.mp4') is True
	assert run_step('job-test-run-step', 1, steps[1], process_step) is False
	assert get_steps('job-test-run-step')[0].get('status') == 'completed'
	assert get_steps('job-test-run-step')[1].get('status') == 'failed'
	assert is_test_output_file('output-2-job-test-run-step-1.mp4') is False
	assert run_step('job-test-run-step', 2, steps[2], process_step) is True
	assert get_steps('job-test-run-step')[2].get('status') == 'completed'
	assert is_directory(get_test_output_path('output-3')) is False
	assert resolve_file_paths(get_test_output_path('output-3-job-test-run-step-2')) == [ get_test_output_path(os.path.join('output-3-job-test-run-step-2', 'target-240p.jpg')) ]


def test_run_steps() -> None:
	args_1 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_path('output-1.mp4')
	}
	args_2 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_path('output-2.mp4')
	}
	args_3 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_path('output-3.jpg')
	}

	assert run_steps('job-invalid', process_step) is False

	create_job('job-test-run-steps')
	add_step('job-test-run-steps', args_1)
	add_step('job-test-run-steps', args_1)
	add_step('job-test-run-steps', args_2)
	add_step('job-test-run-steps', args_3)

	assert run_steps('job-test-run-steps', process_step) is True
	assert get_steps('job-test-run-steps')[0].get('status') == 'completed'
	assert get_steps('job-test-run-steps')[3].get('status') == 'completed'
	assert is_test_output_file('output-1-job-test-run-steps-0.mp4') is True
	assert is_test_output_file('output-1-job-test-run-steps-1.mp4') is True
	assert is_test_output_file('output-2-job-test-run-steps-2.mp4') is True
	assert is_test_output_file('output-3-job-test-run-steps-3.jpg') is True

	args_4 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': 'invalid',
		'output_path': get_test_output_path('output-4.mp4')
	}

	create_job('job-test-run-steps-failed')
	add_step('job-test-run-steps-failed', args_4)
	add_step('job-test-run-steps-failed', args_1)

	assert run_steps('job-test-run-steps-failed', process_step) is False
	assert get_steps('job-test-run-steps-failed')[0].get('status') == 'failed'
	assert get_steps('job-test-run-steps-failed')[1].get('status') == 'drafted'
	assert is_test_output_file('output-1-job-test-run-steps-failed-1.mp4') is False


def test_finalize_steps() -> None:
	args_1 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_path('output-1.mp4')
	}
	args_2 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_path('output-2.mp4')
	}
	args_3 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_path('output-3.jpg')
	}
	args_4 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_path('output-4')
	}
	args_5 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_path('output-4')
	}

	create_job('job-test-finalize-steps')
	add_step('job-test-finalize-steps', args_1)
	add_step('job-test-finalize-steps', args_1)
	add_step('job-test-finalize-steps', args_2)
	add_step('job-test-finalize-steps', args_3)
	add_step('job-test-finalize-steps', args_4)
	add_step('job-test-finalize-steps', args_5)

	copy_file(args_1.get('target_path'), get_test_output_path('output-1-job-test-finalize-steps-0.mp4'))
	copy_file(args_1.get('target_path'), get_test_output_path('output-1-job-test-finalize-steps-1.mp4'))
	copy_file(args_2.get('target_path'), get_test_output_path('output-2-job-test-finalize-steps-2.mp4'))
	copy_file(args_3.get('target_path'), get_test_output_path('output-3-job-test-finalize-steps-3.jpg'))

	temp_directory_1 = get_test_output_path('output-4-job-test-finalize-steps-4')
	temp_directory_2 = get_test_output_path('output-4-job-test-finalize-steps-5')
	create_directory(temp_directory_1)
	create_directory(temp_directory_2)
	copy_file(args_4.get('target_path'), os.path.join(temp_directory_1, '00000001.jpg'))
	copy_file(args_5.get('target_path'), os.path.join(temp_directory_2, '00000002.jpg'))

	assert finalize_steps('job-test-finalize-steps') is True
	assert extract_video_metadata(get_test_output_path('output-1.mp4')).get('frame_total') == 540
	assert extract_video_metadata(get_test_output_path('output-2.mp4')).get('frame_total') == 270
	assert is_test_output_file('output-3.jpg') is True
	assert is_test_output_file('output-3-job-test-finalize-steps-3.jpg') is False
	assert is_test_output_sequence(get_test_output_path('output-4')) is True
	assert resolve_file_paths(get_test_output_path('output-4')) == [ get_test_output_path(os.path.join('output-4', '00000001.jpg')), get_test_output_path(os.path.join('output-4', '00000002.jpg')) ]

	args_6 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_path('output-6.mp4')
	}
	args_7 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_path('output-7.jpg')
	}
	args_8 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_path('output-8')
	}
	args_9 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_path('output-9')
	}

	create_job('job-test-finalize-steps-6')
	add_step('job-test-finalize-steps-6', args_6)
	copy_file(args_6.get('target_path'), get_test_output_path('output-6-job-test-finalize-steps-6-0.mp4'))
	create_directory(get_test_output_path('output-6.mp4'))

	assert finalize_steps('job-test-finalize-steps-6') is False

	create_job('job-test-finalize-steps-7')
	add_step('job-test-finalize-steps-7', args_7)
	copy_file(args_7.get('target_path'), get_test_output_path('output-7-job-test-finalize-steps-7-0.jpg'))
	create_directory(get_test_output_path('output-7.jpg'))

	assert finalize_steps('job-test-finalize-steps-7') is False

	create_job('job-test-finalize-steps-8')
	add_step('job-test-finalize-steps-8', args_8)
	create_directory(get_test_output_path('output-8-job-test-finalize-steps-8-0'))
	copy_file(args_8.get('target_path'), get_test_output_path(os.path.join('output-8-job-test-finalize-steps-8-0', '00000001.jpg')))
	copy_file(args_8.get('target_path'), get_test_output_path('output-8'))

	assert finalize_steps('job-test-finalize-steps-8') is False

	create_job('job-test-finalize-steps-9')
	add_step('job-test-finalize-steps-9', args_9)
	create_directory(get_test_output_path('output-9-job-test-finalize-steps-9-0'))
	copy_file(args_9.get('target_path'), get_test_output_path(os.path.join('output-9-job-test-finalize-steps-9-0', '00000001.jpg')))
	create_directory(get_test_output_path(os.path.join('output-9', '00000001.jpg')))

	assert finalize_steps('job-test-finalize-steps-9') is False


def test_clean_steps() -> None:
	args_1 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_path('output-1.mp4')
	}
	args_2 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_path('output-2.jpg')
	}

	create_job('job-test-clean-steps')
	add_step('job-test-clean-steps', args_1)
	add_step('job-test-clean-steps', args_2)

	copy_file(args_1.get('target_path'), get_test_output_path('output-1-job-test-clean-steps-0.mp4'))
	copy_file(args_2.get('target_path'), get_test_output_path('output-2-job-test-clean-steps-1.jpg'))

	assert is_test_output_file('output-1-job-test-clean-steps-0.mp4') is True
	assert is_test_output_file('output-2-job-test-clean-steps-1.jpg') is True

	assert clean_steps('job-test-clean-steps') is True
	assert is_test_output_file('output-1-job-test-clean-steps-0.mp4') is False
	assert is_test_output_file('output-2-job-test-clean-steps-1.jpg') is False
	assert clean_steps('job-test-clean-steps') is True

	args_3 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_path('output-3')
	}

	add_step('job-test-clean-steps', args_3)
	create_directory(get_test_output_path('output-3-job-test-clean-steps-2'))
	copy_file(args_3.get('target_path'), get_test_output_path(os.path.join('output-3-job-test-clean-steps-2', '00000001.jpg')))

	assert clean_steps('job-test-clean-steps') is True
	assert is_directory(get_test_output_path('output-3-job-test-clean-steps-2')) is False


def test_collect_output_set() -> None:
	args_1 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_path('output-1.mp4')
	}
	args_2 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_path('output-2.mp4')
	}
	args_3 =\
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg'),
		'output_path': get_test_output_path('output-3.jpg')
	}
	args_4 = \
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.mp4'),
		'output_path': get_test_output_path('output-4')
	}

	create_job('job-test-collect-output-set')
	add_step('job-test-collect-output-set', args_1)
	add_step('job-test-collect-output-set', args_1)
	add_step('job-test-collect-output-set', args_2)
	add_step('job-test-collect-output-set', args_3)
	add_step('job-test-collect-output-set', args_4)

	output_set =\
	{
		get_test_output_path('output-1.mp4'):
		[
			get_test_output_path('output-1-job-test-collect-output-set-0.mp4'),
			get_test_output_path('output-1-job-test-collect-output-set-1.mp4')
		],
		get_test_output_path('output-2.mp4'):
		[
			get_test_output_path('output-2-job-test-collect-output-set-2.mp4')
		],
		get_test_output_path('output-3.jpg'):
		[
			get_test_output_path('output-3-job-test-collect-output-set-3.jpg')
		],
		get_test_output_path('output-4'):
		[
			get_test_output_path('output-4-job-test-collect-output-set-4')
		]
	}

	assert collect_output_set('job-invalid') == {}
	assert collect_output_set('job-test-collect-output-set') == output_set

	add_step('job-test-collect-output-set',
	{
		'source_path': get_test_example_file('source.jpg'),
		'target_path': get_test_example_file('target-240p.jpg')
	})

	assert collect_output_set('job-test-collect-output-set') == output_set
