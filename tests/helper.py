import os

from facefusion.temp_helper import get_base_directory_path
from facefusion.typing import JobStatus
from facefusion.filesystem import is_file, is_directory, remove_directory, create_directory


def is_test_job_file(file : str, job_status : JobStatus) -> bool:
	return is_file(get_test_job_file(file, job_status))


def get_test_job_file(file : str, job_status : JobStatus) -> str:
	return os.path.join(get_test_jobs_directory(), job_status, file)


def get_test_jobs_directory() -> str:
	return os.path.join(get_base_directory_path(), 'test-jobs')


def get_test_example_file(file : str) -> str:
	return os.path.join(get_test_examples_directory(), file)


def get_test_examples_directory() -> str:
	return os.path.join(get_base_directory_path(), 'test-examples')


def is_test_output_file(file : str) -> bool:
	return is_file(get_test_output_file(file))


def get_test_output_file(file : str) -> str:
	return os.path.join(get_test_outputs_directory(), file)


def get_test_outputs_directory() -> str:
	return os.path.join(get_base_directory_path(), 'test-outputs')


def prepare_test_output_directory() -> bool:
	test_outputs_directory = get_test_outputs_directory()
	remove_directory(test_outputs_directory)
	create_directory(test_outputs_directory)
	return is_directory(test_outputs_directory)
