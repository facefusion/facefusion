from typing import Dict, List

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK

from facefusion.apis import jobs_helper
from facefusion.types import ProcessId, Task, TaskResponse


async def get_process(request : Request) -> JSONResponse:
	process_set = jobs_helper.collect_process_set()
	process_response : Dict[ProcessId, List[TaskResponse]] = {}

	for process_id, tasks in process_set.items():
		process_response[process_id] = []

		for task in tasks:
			process_response[process_id].append(prepare_task(task))

	return JSONResponse(process_response, status_code = HTTP_200_OK)


def prepare_task(task : Task) -> TaskResponse:
	task_response : TaskResponse =\
	{
		'id': task.get('id'),
		'type': task.get('type'),
		'state': task.get('state'),
		'title': task.get('title'),
		'progress': task.get('progress').copy(),
		'created_at': task.get('created_at').isoformat(),
		'updated_at': task.get('updated_at').isoformat()
	}

	if 'description' in task:
		task_response['description'] = task.get('description')

	return task_response
