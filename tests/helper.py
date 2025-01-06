import os
import tempfile
from pathlib import Path

from facefusion.filesystem import create_directory, is_directory, is_file, remove_directory
from facefusion.typing import JobStatus


# Get the base temporary directory once and reuse it
TEMP_DIR = Path(tempfile.gettempdir())

def is_test_job_file(file_path: str, job_status: JobStatus) -> bool:
    return is_file(get_test_job_file(file_path, job_status))


def get_test_job_file(file_path: str, job_status: JobStatus) -> str:
    return str(get_test_jobs_directory() / job_status / file_path)


def get_test_jobs_directory() -> Path:
    return TEMP_DIR / 'facefusion-test-jobs'


def get_test_example_file(file_path: str) -> str:
    return str(get_test_examples_directory() / file_path)


def get_test_examples_directory() -> Path:
    return TEMP_DIR / 'facefusion-test-examples'


def is_test_output_file(file_path: str) -> bool:
    return is_file(get_test_output_file(file_path))


def get_test_output_file(file_path: str) -> str:
    return str(get_test_outputs_directory() / file_path)


def get_test_outputs_directory() -> Path:
    return TEMP_DIR / 'facefusion-test-outputs'


def prepare_test_output_directory() -> bool:
    test_outputs_directory = get_test_outputs_directory()
    try:
        remove_directory(str(test_outputs_directory))  # Ensure it's removed
        create_directory(str(test_outputs_directory))  # Ensure it's created
        return is_directory(str(test_outputs_directory))
    except Exception as e:
        # Log the error or handle it as needed
        print(f"Error preparing test output directory: {e}")
        return False
