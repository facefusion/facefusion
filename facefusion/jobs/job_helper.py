import os
from datetime import datetime
from typing import Optional

from facefusion.filesystem import get_file_extension, get_file_name


def get_step_output_path(job_id : str, step_index : int, output_path : str) -> Optional[str]:
	if output_path:
		output_directory_path, output_file_path = os.path.split(output_path)
		output_file_name = get_file_name(output_file_path)
		output_file_extension = get_file_extension(output_file_path)

		if output_file_name and output_file_extension:
			return os.path.join(output_directory_path, output_file_name + '-' + job_id + '-' + str(step_index) + output_file_extension)
	return None


def suggest_job_id(job_prefix : str = 'job') -> str:
	return job_prefix + '-' + datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
