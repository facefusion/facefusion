from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

import facefusion.choices
from facefusion import state_manager, translator
from facefusion.jobs import job_helper, job_manager


async def get_jobs(request : Request) -> JSONResponse:
	job_status = request.query_params.get('status')

	if job_status in facefusion.choices.job_statuses:
		job_set = job_manager.find_jobs(job_status)
		job_summaries = {}

		for job_id, job in job_set.items():
			job_summaries[job_id] =\
			{
				'version': job.get('version'),
				'date_created': job.get('date_created'),
				'date_updated': job.get('date_updated')
			}

		return JSONResponse(job_summaries, status_code = HTTP_200_OK)

	return JSONResponse(
	{
		'message': translator.get('invalid_job_status', 'facefusion.apis')
	}, status_code = HTTP_400_BAD_REQUEST)


async def get_job(request : Request) -> JSONResponse:
	job_id = request.path_params.get('job_id')
	job = job_manager.read_job_file(job_id)

	if job:
		return JSONResponse(job, status_code = HTTP_200_OK)

	return JSONResponse(
	{
		'message': translator.get('job_not_found', 'facefusion.apis')
	}, status_code = HTTP_404_NOT_FOUND)


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


async def delete_jobs(request : Request) -> JSONResponse:
	if job_manager.delete_jobs(state_manager.get_item('halt_on_error')):
		return JSONResponse(
		{
			'message': translator.get('ok', 'facefusion.apis')
		}, status_code = HTTP_200_OK)

	return JSONResponse(
	{
		'message': translator.get('job_not_found', 'facefusion.apis')
	}, status_code = HTTP_404_NOT_FOUND)


async def delete_job(request : Request) -> JSONResponse:
	job_id = request.path_params.get('job_id')

	if job_manager.delete_job(job_id):
		return JSONResponse(
		{
			'message': translator.get('ok', 'facefusion.apis')
		}, status_code = HTTP_200_OK)

	return JSONResponse(
	{
		'message': translator.get('job_not_found', 'facefusion.apis')
	}, status_code = HTTP_404_NOT_FOUND)
