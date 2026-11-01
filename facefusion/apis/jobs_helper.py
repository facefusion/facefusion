from facefusion import process_manager, session_context, session_manager
from facefusion.apis import asset_store
from facefusion.filesystem import is_file
from facefusion.jobs import job_manager
from facefusion.types import JobId, ProcessSet


def create_output_asset(job_id : JobId) -> None:
	job = job_manager.read_job_file(job_id)

	if job and job.get('steps'):
		output_path = job.get('steps')[-1].get('args').get('output_path')

		if output_path and is_file(output_path):
			asset_store.create_asset('output', output_path)


def stop_fork_session() -> None:
	owner_id = session_manager.resolve_owner_id()
	fork_id = session_manager.find_fork_session_id(owner_id)

	if fork_id:
		session_context.set_session_id(fork_id)
		process_manager.stop_process()
		session_context.set_session_id(owner_id)


def collect_process_set() -> ProcessSet:
	owner_id = session_manager.resolve_owner_id()
	fork_id = session_manager.find_fork_session_id(owner_id)
	process_set = process_manager.get_process_set().copy()

	if fork_id:
		session_context.set_session_id(fork_id)
		process_set.update(process_manager.get_process_set())
		session_context.set_session_id(owner_id)

	return process_set
