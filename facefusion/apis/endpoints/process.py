from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK

from facefusion.apis import jobs_helper


async def get_process(request : Request) -> JSONResponse:
	__process_set__ = {}
	process_set = jobs_helper.collect_process_set()

	for process_id, tasks in process_set.items():
		__tasks__ = []

		for task in tasks:
			__tasks__.append(
			{
				'id': task.get('id'),
				'type': task.get('type'),
				'state': task.get('state'),
				'title': task.get('title'),
				'description': task.get('description'),
				'progress': task.get('progress'),
				'created_at': task.get('created_at').isoformat(),
				'updated_at': task.get('updated_at').isoformat()
			})

		__process_set__[process_id] = __tasks__

	return JSONResponse(__process_set__, status_code = HTTP_200_OK)
