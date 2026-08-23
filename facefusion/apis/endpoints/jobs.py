from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST

from facefusion import translator
from facefusion.jobs import job_helper, job_manager


async def create_job(request : Request) -> JSONResponse:
	job_id = job_helper.suggest_job_id()

	if job_manager.create_job(job_id):
		return JSONResponse(
		{
			'job_id': job_id
		}, status_code = HTTP_201_CREATED)

	return JSONResponse(
	{
		'message': translator.get('job_not_created', 'facefusion.apis')
	}, status_code = HTTP_400_BAD_REQUEST)
