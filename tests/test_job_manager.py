import shutil
import json

import pytest

from typing import Any
from facefusion.job_manager import init_jobs, clear_jobs, create_job, add_step, remove_step, get_step_total, insert_step, move_job_file, delete_job_file, get_job_status


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	jobs_path = '.jobs'
	clear_jobs(jobs_path)
	init_jobs(jobs_path)


def read_json(json_path : str) -> Any:
	with open(json_path, 'r') as json_file:
		return json.load(json_file)


def test_create_job() -> None:
	create_job('test_create_job')

	job_actual = read_json('.jobs/queued/test_create_job.json')
	job_expect = read_json('tests/providers/test_create_job.json')

	assert job_actual.get('version') == job_expect.get('version')
	assert job_actual.get('date_created')
	assert job_actual.get('date_updated') is None
	assert job_actual.get('steps') == job_expect.get('steps')
	assert get_step_total('test_create_job') == 0


def test_add_step() -> None:
	shutil.copyfile('tests/providers/test_job_add_step.json', '.jobs/queued/test_job_add_step.json')

	assert get_step_total('test_job_add_step') == 0
	assert add_step('test_job_add_step',
	{
		'source_paths':
		[
			'source-a.jpg',
			'source-b.jpg'
		],
		'target': 'target-a.jpg',
		'output_path': 'output'
	})
	assert get_step_total('test_job_add_step') == 1


def test_insert_step() -> None:
	shutil.copyfile('tests/providers/test_job_insert_step.json', '.jobs/queued/test_job_insert_step.json')

	assert get_step_total('test_job_insert_step') == 1

	step =\
	{
		'source_paths': [ '123.jpg' ],
		'target_path': '456.jpg',
		'output_path': 'output'
	}
	assert insert_step('test_job_insert_step', 0, step)
	assert get_step_total('test_job_insert_step') == 2

	job = read_json('.jobs/queued/test_job_insert_step.json')

	assert job.get('steps')[0].get('args') == step

	step =\
	{
		'source_paths': [ 'abc.jpg' ],
		'target_path': 'def.jpg',
		'output_path': 'output'
	}
	assert insert_step('test_job_insert_step', -1, step)
	assert get_step_total('test_job_insert_step') == 3

	job = read_json('.jobs/queued/test_job_insert_step.json')

	assert job.get('steps')[-1].get('args') == step


def test_remove_step() -> None:
	shutil.copyfile('tests/providers/test_job_remove_step.json', '.jobs/queued/test_job_remove_step.json')

	assert get_step_total('test_job_remove_step') == 3
	assert remove_step('test_job_remove_step', 0)
	assert get_step_total('test_job_remove_step') == 2

	job = read_json('.jobs/queued/test_job_remove_step.json')

	assert (job.get('steps')[0].get('args') ==\
	{
		'source_paths': ['123.jpg'],
		'target_path': '456.jpg',
		'output_path': 'output'
	})

	assert remove_step('test_job_remove_step', -1)
	assert get_step_total('test_job_remove_step') == 1

	job = read_json('.jobs/queued/test_job_remove_step.json')

	assert job.get('steps')[0].get('args') ==\
	{
		'source_paths': ['123.jpg'],
		'target_path': '456.jpg',
		'output_path': 'output'
	}


def test_move_job() -> None:
	shutil.copyfile('tests/providers/test_move_job.json', '.jobs/queued/test_move_job.json')

	assert move_job_file('test_move_job', 'failed')
	assert get_job_status('test_move_job') == 'failed'
	assert move_job_file('test_move_job', 'completed')
	assert get_job_status('test_move_job') == 'completed'
	assert move_job_file('test_move_job', 'queued')
	assert get_job_status('test_move_job') == 'queued'


def test_delete_job() -> None:
	shutil.copyfile('tests/providers/test_delete_job.json', '.jobs/queued/test_delete_job.json')
	assert delete_job_file('test_delete_job')
