from facefusion import process_manager, session_context, session_manager
from facefusion.apis import asset_store
from facefusion.filesystem import is_file
from facefusion.jobs import job_manager


def create_output_asset(job_id : str) -> None:
	job = job_manager.read_job_file(job_id)

	if job and job.get('steps'):
		output_path = job.get('steps')[-1].get('args').get('output_path')

		if output_path and is_file(output_path):
			asset_store.create_asset('output', output_path)


def stop_fork_session() -> None:
	owner_id = session_manager.resolve_owner_id()
	fork_id = session_manager.find_cli_session_id(owner_id)

	if fork_id:
		session_context.set_session_id(fork_id)
		process_manager.stop()
		session_context.set_session_id(owner_id)
