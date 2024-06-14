import os
import shutil

from facefusion.temp_helper import get_temp_base_path
from facefusion.typing import JobStatus
from facefusion.filesystem import is_file


def get_test_jobs_directory() -> str:
	return os.path.join(get_temp_base_path(), 'test-jobs')


def get_test_examples_directory() -> str:
	return os.path.join(get_temp_base_path(), 'test-examples')


def get_test_outputs_directory() -> str:
	return os.path.join(get_temp_base_path(), 'test-outputs')


def prepare_test_output_directory() -> None:
	shutil.rmtree(get_test_outputs_directory(), ignore_errors = True)
	os.mkdir(get_test_outputs_directory())


def get_test_job_file(file : str, job_status : JobStatus) -> str:
	return os.path.join(get_temp_base_path(), 'test-jobs', job_status, file)


def get_test_example_file(file : str) -> str:
	return os.path.join(get_temp_base_path(), 'test-examples', file)


def get_test_output_file(file : str) -> str:
	return os.path.join(get_temp_base_path(), 'test-outputs', file)


def is_test_job_file(file : str, job_status : JobStatus) -> bool:
	return is_file(get_test_job_file(file, job_status))


def is_test_output_file(file : str) -> bool:
	return is_file(get_test_output_file(file))
