import os
from functools import partial

from starlette.background import BackgroundTask, BackgroundTasks
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_202_ACCEPTED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND

import facefusion.choices
import facefusion.core
from facefusion import args_helper, session_context, session_manager, state_manager, translator
from facefusion.apis import jobs_helper
from facefusion.apis.session_helper import extract_access_token
from facefusion.filesystem import create_directory, get_file_extension, is_directory
from facefusion.jobs import job_helper, job_manager, job_runner


async def get_jobs(request : Request) -> JSONResponse:
	job_status = request.query_params.get('status')

	if job_status in facefusion.choices.job_statuses:
		__job_set__ = {}
		job_set = job_manager.find_jobs(job_status)

		for job_id, job in job_set.items():
			__job_set__[job_id] =\
			{
				'version': job.get('version'),
				'date_created': job.get('date_created'),
				'date_updated': job.get('date_updated')
			}

		return JSONResponse(__job_set__, status_code = HTTP_200_OK)

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


async def update_jobs(request : Request) -> JSONResponse:
	action = request.query_params.get('action')

	if action == 'submit':
		if job_manager.submit_jobs(state_manager.get_item('halt_on_error')):
			return JSONResponse(
			{
				'message': translator.get('ok', 'facefusion.apis')
			}, status_code = HTTP_200_OK)

		return JSONResponse(
		{
			'message': translator.get('job_all_not_submitted', 'facefusion.apis')
		}, status_code = HTTP_400_BAD_REQUEST)

	if action == 'run':
		if job_manager.find_job_ids('queued'):
			run_jobs_task = BackgroundTask(partial(job_runner.run_jobs, facefusion.core.process_step, state_manager.get_item('halt_on_error')))

			return JSONResponse(
			{
				'message': translator.get('ok', 'facefusion.apis')
			}, status_code = HTTP_202_ACCEPTED, background = run_jobs_task)

		return JSONResponse(
		{
			'message': translator.get('job_all_not_run', 'facefusion.apis')
		}, status_code = HTTP_400_BAD_REQUEST)

	if action == 'retry':
		if job_manager.find_job_ids('failed'):
			retry_jobs_task = BackgroundTask(partial(job_runner.retry_jobs, facefusion.core.process_step, state_manager.get_item('halt_on_error')))

			return JSONResponse(
			{
				'message': translator.get('ok', 'facefusion.apis')
			}, status_code = HTTP_202_ACCEPTED, background = retry_jobs_task)

		return JSONResponse(
		{
			'message': translator.get('job_all_not_retried', 'facefusion.apis')
		}, status_code = HTTP_400_BAD_REQUEST)

	return JSONResponse(
	{
		'message': translator.get('invalid_job_action', 'facefusion.apis')
	}, status_code = HTTP_400_BAD_REQUEST)


async def update_job(request : Request) -> JSONResponse:
	job_id = request.path_params.get('job_id')
	action = request.query_params.get('action')
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)

	if action == 'submit':
		if job_manager.submit_job(job_id):
			return JSONResponse(
			{
				'message': translator.get('ok', 'facefusion.apis')
			}, status_code = HTTP_200_OK)

		return JSONResponse(
		{
			'message': translator.get('job_not_submitted', 'facefusion.apis')
		}, status_code = HTTP_400_BAD_REQUEST)

	if action == 'run':
		if job_id in job_manager.find_job_ids('queued'):
			run_job_tasks = BackgroundTasks()
			run_job_tasks.add_task(partial(job_runner.run_job, job_id, facefusion.core.process_step))
			run_job_tasks.add_task(partial(jobs_helper.capture_output_asset, job_id, session_id))

			return JSONResponse(
			{
				'message': translator.get('ok', 'facefusion.apis')
			}, status_code = HTTP_202_ACCEPTED, background = run_job_tasks)

		return JSONResponse(
		{
			'message': translator.get('job_not_run', 'facefusion.apis')
		}, status_code = HTTP_400_BAD_REQUEST)

	if action == 'retry':
		if job_id in job_manager.find_job_ids('failed'):
			retry_job_tasks = BackgroundTasks()
			retry_job_tasks.add_task(partial(job_runner.retry_job, job_id, facefusion.core.process_step))
			retry_job_tasks.add_task(partial(jobs_helper.capture_output_asset, job_id, session_id))

			return JSONResponse(
			{
				'message': translator.get('ok', 'facefusion.apis')
			}, status_code = HTTP_202_ACCEPTED, background = retry_job_tasks)

		return JSONResponse(
		{
			'message': translator.get('job_not_retried', 'facefusion.apis')
		}, status_code = HTTP_400_BAD_REQUEST)

	return JSONResponse(
	{
		'message': translator.get('invalid_job_action', 'facefusion.apis')
	}, status_code = HTTP_400_BAD_REQUEST)


async def delete_jobs(request : Request) -> JSONResponse:
	if job_manager.delete_jobs(state_manager.get_item('halt_on_error')):
		return JSONResponse(
		{
			'message': translator.get('ok', 'facefusion.apis')
		}, status_code = HTTP_200_OK)

	return JSONResponse(
	{
		'message': translator.get('job_all_not_deleted', 'facefusion.apis')
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
		'message': translator.get('job_not_deleted', 'facefusion.apis')
	}, status_code = HTTP_404_NOT_FOUND)


async def create_step(request : Request) -> JSONResponse:
	job_id = request.path_params.get('job_id')
	step_index = request.path_params.get('step_index')
	action = request.query_params.get('action')

	step_args = await request.json()
	step_args = args_helper.filter_api_step_args(step_args)

	if state_manager.get_item('source_paths'):
		step_args['source_paths'] = state_manager.get_item('source_paths')

	if state_manager.get_item('target_path'):
		access_token = extract_access_token(request.scope)
		session_id = session_manager.find_session_id(access_token)
		session_context.set_session_id(session_id)
		temp_path = state_manager.resolve_temp_path()

		step_args['target_path'] = state_manager.get_item('target_path')

		if is_directory(temp_path) or create_directory(temp_path):
			step_args['output_path'] = os.path.join(temp_path, job_id + get_file_extension(state_manager.get_item('target_path')))

	if action == 'add':
		if job_manager.add_step(job_id, step_args):
			return JSONResponse(
			{
				'message': translator.get('ok', 'facefusion.apis')
			}, status_code = HTTP_201_CREATED)

		return JSONResponse(
		{
			'message': translator.get('job_step_not_added', 'facefusion.apis')
		}, status_code = HTTP_400_BAD_REQUEST)

	if action == 'insert':
		if job_manager.insert_step(job_id, step_index, step_args):
			return JSONResponse(
			{
				'message': translator.get('ok', 'facefusion.apis')
			}, status_code = HTTP_201_CREATED)

		return JSONResponse(
		{
			'message': translator.get('job_step_not_inserted', 'facefusion.apis')
		}, status_code = HTTP_400_BAD_REQUEST)

	if action == 'remix':
		if job_manager.remix_step(job_id, step_index, step_args):
			return JSONResponse(
			{
				'message': translator.get('ok', 'facefusion.apis')
			}, status_code = HTTP_201_CREATED)

		return JSONResponse(
		{
			'message': translator.get('job_step_not_remixed', 'facefusion.apis')
		}, status_code = HTTP_400_BAD_REQUEST)

	return JSONResponse(
	{
		'message': translator.get('invalid_job_action', 'facefusion.apis')
	}, status_code = HTTP_400_BAD_REQUEST)


async def delete_step(request : Request) -> JSONResponse:
	job_id = request.path_params.get('job_id')
	step_index = request.path_params.get('step_index')

	if job_manager.remove_step(job_id, step_index):
		return JSONResponse(
		{
			'message': translator.get('ok', 'facefusion.apis')
		}, status_code = HTTP_200_OK)

	return JSONResponse(
	{
		'message': translator.get('job_step_not_removed', 'facefusion.apis')
	}, status_code = HTTP_404_NOT_FOUND)
