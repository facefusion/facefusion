import os
import shutil
import tempfile

from facefusion.filesystem import is_file


def get_test_jobs_directory() -> str:
	return os.path.join(tempfile.gettempdir(), 'test-jobs')


def get_test_examples_directory() -> str:
	return os.path.join(tempfile.gettempdir(), 'test-examples')


def get_test_outputs_directory() -> str:
	return os.path.join(tempfile.gettempdir(), 'test-outputs')


def prepare_test_output_directory() -> None:
	shutil.rmtree(get_test_outputs_directory(), ignore_errors = True)
	os.mkdir(get_test_outputs_directory())


def get_test_example_file(file : str) -> str:
	return os.path.join(tempfile.gettempdir(), 'test-examples', file)


def get_test_output_file(file : str) -> str:
	return os.path.join(tempfile.gettempdir(), 'test-outputs', file)


def is_test_output_file(file : str) -> bool:
	return is_file(get_test_output_file(file))
