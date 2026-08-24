from facefusion.apis import asset_store
from facefusion.filesystem import is_file
from facefusion.jobs import job_manager
from facefusion.types import SessionId


def capture_output_asset(job_id : str, session_id : SessionId) -> None:
	job = job_manager.read_job_file(job_id)

	if job and job.get('steps'):
		output_path = job.get('steps')[-1].get('args').get('output_path')

		if output_path and is_file(output_path):
			asset_store.create_asset(session_id, 'output', output_path)
