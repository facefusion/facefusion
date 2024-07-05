import hashlib
import os
from time import sleep
from typing import Optional, Tuple

import gradio

from facefusion import process_manager, state_manager, wording
from facefusion.core import create_program, process_step
from facefusion.filesystem import is_directory, is_image, is_video
from facefusion.jobs import job_helper, job_manager, job_runner, job_store
from facefusion.memory import limit_system_memory
from facefusion.program_helper import import_state, reduce_args
from facefusion.temp_helper import clear_temp_directory
from facefusion.uis.core import get_ui_component

INSTANT_RUNNER_START_BUTTON : Optional[gradio.Button] = None
INSTANT_RUNNER_STOP_BUTTON : Optional[gradio.Button] = None
INSTANT_RUNNER_CLEAR_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global INSTANT_RUNNER_START_BUTTON
	global INSTANT_RUNNER_STOP_BUTTON
	global INSTANT_RUNNER_CLEAR_BUTTON

	INSTANT_RUNNER_START_BUTTON = gradio.Button(
		value = wording.get('uis.start_button'),
		variant = 'primary',
		size = 'sm'
	)
	INSTANT_RUNNER_STOP_BUTTON = gradio.Button(
		value = wording.get('uis.stop_button'),
		variant = 'primary',
		size = 'sm',
		visible = False
	)
	INSTANT_RUNNER_CLEAR_BUTTON = gradio.Button(
		value = wording.get('uis.clear_button'),
		size = 'sm'
	)


def listen() -> None:
	output_image = get_ui_component('output_image')
	output_video = get_ui_component('output_video')

	if output_image and output_video:
		INSTANT_RUNNER_START_BUTTON.click(start, outputs = [ INSTANT_RUNNER_START_BUTTON, INSTANT_RUNNER_STOP_BUTTON ])
		INSTANT_RUNNER_START_BUTTON.click(process, outputs = [ INSTANT_RUNNER_START_BUTTON, INSTANT_RUNNER_STOP_BUTTON, output_image, output_video ])
		INSTANT_RUNNER_STOP_BUTTON.click(stop, outputs = [ INSTANT_RUNNER_START_BUTTON, INSTANT_RUNNER_STOP_BUTTON ])
		INSTANT_RUNNER_CLEAR_BUTTON.click(clear, outputs = [ output_image, output_video ])


def start() -> Tuple[gradio.Button, gradio.Button]:
	while not process_manager.is_processing():
		sleep(0.5)
	return gradio.Button(visible = False), gradio.Button(visible = True)


def process() -> Tuple[gradio.Button, gradio.Button, gradio.Image, gradio.Video]:
	output_path = state_manager.get_item('output_path')
	temp_output_path = state_manager.get_item('output_path')

	if state_manager.get_item('system_memory_limit') > 0:
		limit_system_memory(state_manager.get_item('system_memory_limit'))
	if is_directory(temp_output_path):
		temp_output_path = suggest_output_path(temp_output_path, state_manager.get_item('target_path'))
	if job_manager.init_jobs(state_manager.get_item('jobs_path')):
		state_manager.set_item('output_path', temp_output_path)
		create_and_run_job()
		state_manager.set_item('output_path', output_path)
	if is_image(temp_output_path):
		return gradio.Button(visible = True), gradio.Button(visible = False), gradio.Image(value = temp_output_path, visible = True), gradio.Video(value = None, visible = False)
	if is_video(temp_output_path):
		return gradio.Button(visible = True), gradio.Button(visible = False), gradio.Image(value = None, visible = False), gradio.Video(value = temp_output_path, visible = True)
	return gradio.Button(visible = True), gradio.Button(visible = False), gradio.Image(value = None), gradio.Video(value = None)


def suggest_output_path(output_directory_path : str, target_path : str) -> Optional[str]:
	if is_image(target_path) or is_video(target_path):
		_, target_extension = os.path.splitext(target_path)
		output_name = hashlib.sha1(str(state_manager.get_state()).encode('utf-8')).hexdigest()[:8]
		return os.path.join(output_directory_path, output_name + target_extension)
	return None


def create_and_run_job() -> bool:
	job_id = job_helper.suggest_job_id('ui')
	program = create_program()
	program = import_state(program, job_store.get_step_keys(), state_manager.get_state())
	program = reduce_args(program, job_store.get_step_keys())
	step_args = vars(program.parse_args())

	return job_manager.create_job(job_id) and job_manager.add_step(job_id, step_args) and job_manager.submit_job(job_id) and job_runner.run_job(job_id, process_step)


def stop() -> Tuple[gradio.Button, gradio.Button]:
	process_manager.stop()
	return gradio.Button(visible = True), gradio.Button(visible = False)


def clear() -> Tuple[gradio.Image, gradio.Video]:
	while process_manager.is_processing():
		sleep(0.5)
	if state_manager.get_item('target_path'):
		clear_temp_directory(state_manager.get_item('target_path'))
	return gradio.Image(value = None), gradio.Video(value = None)
