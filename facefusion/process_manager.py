import secrets
from datetime import datetime
from typing import List, Optional

from facefusion import store_creator
from facefusion.session_context import get_session_id
from facefusion.types import ProcessId, ProcessSet, Progress, SessionId, Store, Task, TaskId, TaskState, TaskType

PROCESS_STORE : Store = store_creator.create_store({})


def init() -> None:
	session_id = get_session_id()
	store_creator.init_content(PROCESS_STORE, session_id)


def clear() -> None:
	session_id = get_session_id()
	store_creator.init_content(PROCESS_STORE, session_id)


def destroy(session_id : SessionId) -> None:
	store_creator.delete_content(PROCESS_STORE, session_id)


def start_process() -> ProcessId:
	session_id = get_session_id()
	process_id = secrets.token_urlsafe(16)
	process_set = get_process_set().copy()
	process_set[process_id] = []
	store_creator.set_content(PROCESS_STORE, session_id, process_set)
	return process_id


def stop_process() -> None:
	task = get_task()

	if task:
		task['state'] = 'stopping'
		task['updated_at'] = datetime.now()


def end_process() -> None:
	task = get_task()

	if task:
		task['state'] = 'pending'
		task['updated_at'] = datetime.now()


def get_process_set() -> ProcessSet:
	session_id = get_session_id()
	process_set : ProcessSet = {}

	if store_creator.get_content(PROCESS_STORE, session_id):
		process_set = store_creator.get_content(PROCESS_STORE, session_id)

	return process_set


def get_process_id() -> Optional[ProcessId]:
	process_set = get_process_set()

	if process_set:
		return list(process_set.keys())[-1]

	return None


def get_process_state() -> TaskState:
	task = get_task()

	if task:
		return task.get('state')

	return 'pending'


def is_process_pending() -> bool:
	return get_process_state() == 'pending'


def is_process_checking() -> bool:
	return get_process_state() == 'checking'


def is_process_processing() -> bool:
	return get_process_state() == 'processing'


def is_process_stopping() -> bool:
	return get_process_state() == 'stopping'


def start_task(task_type : TaskType, title : str, progress : Progress) -> TaskId:
	task_id = secrets.token_urlsafe(16)
	date_time = datetime.now()
	task_state : TaskState = 'processing'

	if task_type == 'download':
		task_state = 'checking'

	if is_process_stopping():
		task_state = 'stopping'
		end_process()

	get_tasks().append(
	{
		'id': task_id,
		'type': task_type,
		'state': task_state,
		'title': title,
		'progress': progress.copy(),
		'created_at': date_time,
		'updated_at': date_time
	})
	return task_id


def describe_task(description : str) -> None:
	task = get_task()
	task['description'] = description


def update_task() -> None:
	task = get_task()
	seek_task(task.get('progress').get('current') + 1)


def seek_task(current : int) -> None:
	task = get_task()
	task['progress']['current'] = current
	task['updated_at'] = datetime.now()


def end_task() -> None:
	task = get_task()

	if not is_process_stopping():
		if 'total' in task.get('progress'):
			task['progress']['current'] = task.get('progress').get('total')
		task['state'] = 'pending'

	task['updated_at'] = datetime.now()


def get_tasks() -> List[Task]:
	process_set = get_process_set()
	process_id = get_process_id()
	tasks : List[Task] = []

	if process_id:
		tasks = process_set.get(process_id)

	return tasks


def get_task() -> Optional[Task]:
	tasks = get_tasks()

	if tasks:
		return tasks[-1]

	return None


def collect_tasks() -> List[Task]:
	tasks : List[Task] = []

	for process_set in list(PROCESS_STORE.get('content_set').values()):
		for __tasks__ in list(process_set.values()):
			tasks.extend(__tasks__)

	return tasks
