from typing import Tuple, Optional
import hashlib
import os
import tempfile
from time import sleep
import gradio

import facefusion.globals
from facefusion import process_manager, state_manager, wording
from facefusion.core import process_step, create_program
from facefusion.memory import limit_system_memory
from facefusion.jobs import job_manager, job_runner, job_store, job_helper
from facefusion.program_helper import reduce_args, import_globals, import_state
from facefusion.filesystem import is_image, is_video, is_directory
from facefusion.temp_helper import clear_temp_directory

OUTPUT_PATH_TEXTBOX : Optional[gradio.Textbox] = None
OUTPUT_IMAGE : Optional[gradio.Image] = None
OUTPUT_VIDEO : Optional[gradio.Video] = None
OUTPUT_START_BUTTON : Optional[gradio.Button] = None
OUTPUT_CLEAR_BUTTON : Optional[gradio.Button] = None
OUTPUT_STOP_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global OUTPUT_PATH_TEXTBOX
	global OUTPUT_IMAGE
	global OUTPUT_VIDEO
	global OUTPUT_START_BUTTON
	global OUTPUT_STOP_BUTTON
	global OUTPUT_CLEAR_BUTTON

	if not state_manager.get_item('output_path'):
		state_manager.set_item('output_path', tempfile.gettempdir())
	OUTPUT_PATH_TEXTBOX = gradio.Textbox(
		label = wording.get('uis.output_path_textbox'),
		value = state_manager.get_item('output_path'),
		max_lines = 1
	)
	OUTPUT_IMAGE = gradio.Image(
		label = wording.get('uis.output_image_or_video'),
		visible = False
	)
	OUTPUT_VIDEO = gradio.Video(
		label = wording.get('uis.output_image_or_video')
	)
	OUTPUT_START_BUTTON = gradio.Button(
		value = wording.get('uis.start_button'),
		variant = 'primary',
		size = 'sm'
	)
	OUTPUT_STOP_BUTTON = gradio.Button(
		value = wording.get('uis.stop_button'),
		variant = 'primary',
		size = 'sm',
		visible = False
	)
	OUTPUT_CLEAR_BUTTON = gradio.Button(
		value = wording.get('uis.clear_button'),
		size = 'sm'
	)


def listen() -> None:
	OUTPUT_PATH_TEXTBOX.change(update_output_path, inputs = OUTPUT_PATH_TEXTBOX)
	OUTPUT_START_BUTTON.click(start, outputs = [ OUTPUT_START_BUTTON, OUTPUT_STOP_BUTTON ])
	OUTPUT_START_BUTTON.click(process, outputs = [ OUTPUT_IMAGE, OUTPUT_VIDEO, OUTPUT_START_BUTTON, OUTPUT_STOP_BUTTON ])
	OUTPUT_STOP_BUTTON.click(stop, outputs = [ OUTPUT_START_BUTTON, OUTPUT_STOP_BUTTON ])
	OUTPUT_CLEAR_BUTTON.click(clear, outputs = [ OUTPUT_IMAGE, OUTPUT_VIDEO ])


def start() -> Tuple[gradio.Button, gradio.Button]:
	while not process_manager.is_processing():
		sleep(0.5)
	return gradio.Button(visible = False), gradio.Button(visible = True)


def process() -> Tuple[gradio.Image, gradio.Video, gradio.Button, gradio.Button]:
	output_path = state_manager.get_item('output_path')
	stored_output_path = state_manager.get_item('output_path')

	if facefusion.globals.system_memory_limit > 0:
		limit_system_memory(facefusion.globals.system_memory_limit)
	if is_directory(output_path):
		output_path = suggest_output_path(output_path, state_manager.get_item('target_path'))
	if job_manager.init_jobs(state_manager.get_item('jobs_path')):
		state_manager.set_item('output_path', output_path)
		create_and_run_job()
		state_manager.set_item('output_path', stored_output_path)
	if is_image(output_path):
		return gradio.Image(value = output_path, visible = True), gradio.Video(value = None, visible = False), gradio.Button(visible = True), gradio.Button(visible = False)
	if is_video(output_path):
		return gradio.Image(value = None, visible = False), gradio.Video(value = output_path, visible = True), gradio.Button(visible = True), gradio.Button(visible = False)
	return gradio.Image(value = None), gradio.Video(value = None), gradio.Button(visible = True), gradio.Button(visible = False)


def suggest_output_path(output_directory_path : str, target_path : str) -> Optional[str]:
	if is_image(target_path) or is_video(target_path):
		_, target_extension = os.path.splitext(target_path)
		output_name = hashlib.sha1(str(state_manager.get_state()).encode('utf-8')).hexdigest()[:8]
		return os.path.join(output_directory_path, output_name + target_extension)
	return None


def create_and_run_job() -> bool:
	job_id = job_helper.suggest_job_id('ui')
	program = create_program()
	program = import_globals(program, job_store.get_step_keys(), [ facefusion ])
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


def update_output_path(output_path : str) -> None:
	state_manager.set_item('output_path', output_path)
