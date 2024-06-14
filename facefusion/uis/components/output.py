from typing import Tuple, Optional
from time import sleep
import gradio

import facefusion.globals
from facefusion import process_manager, wording
from facefusion.core import process_step, create_program
from facefusion.memory import limit_system_memory
from facefusion.jobs import job_manager, job_runner, job_store, job_helper
from facefusion.program_helper import reduce_args, import_globals
from facefusion.uis.core import get_ui_component
from facefusion.filesystem import is_image, is_video
from facefusion.temp_helper import clear_temp
import facefusion.processors.frame

OUTPUT_IMAGE : Optional[gradio.Image] = None
OUTPUT_VIDEO : Optional[gradio.Video] = None
OUTPUT_START_BUTTON : Optional[gradio.Button] = None
OUTPUT_CLEAR_BUTTON : Optional[gradio.Button] = None
OUTPUT_STOP_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global OUTPUT_IMAGE
	global OUTPUT_VIDEO
	global OUTPUT_START_BUTTON
	global OUTPUT_STOP_BUTTON
	global OUTPUT_CLEAR_BUTTON

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
	output_path_textbox = get_ui_component('output_path_textbox')
	if output_path_textbox:
		OUTPUT_START_BUTTON.click(start, outputs = [ OUTPUT_START_BUTTON, OUTPUT_STOP_BUTTON ])
		OUTPUT_START_BUTTON.click(process, outputs = [ OUTPUT_IMAGE, OUTPUT_VIDEO, OUTPUT_START_BUTTON, OUTPUT_STOP_BUTTON ])
	OUTPUT_STOP_BUTTON.click(stop, outputs = [ OUTPUT_START_BUTTON, OUTPUT_STOP_BUTTON ])
	OUTPUT_CLEAR_BUTTON.click(clear, outputs = [ OUTPUT_IMAGE, OUTPUT_VIDEO ])


def start() -> Tuple[gradio.Button, gradio.Button]:
	while not process_manager.is_processing():
		sleep(0.5)
	return gradio.Button(visible = False), gradio.Button(visible = True)


def process() -> Tuple[gradio.Image, gradio.Video, gradio.Button, gradio.Button]:
	if facefusion.globals.system_memory_limit > 0:
		limit_system_memory(facefusion.globals.system_memory_limit)
	if job_manager.init_jobs(facefusion.globals.jobs_path):
		create_and_run_job()
	if is_image(facefusion.globals.output_path):
		return gradio.Image(value = facefusion.globals.output_path, visible = True), gradio.Video(value = None, visible = False), gradio.Button(visible = True), gradio.Button(visible = False)
	if is_video(facefusion.globals.output_path):
		return gradio.Image(value = None, visible = False), gradio.Video(value = facefusion.globals.output_path, visible = True), gradio.Button(visible = True), gradio.Button(visible = False)
	return gradio.Image(value = None), gradio.Video(value = None), gradio.Button(visible = True), gradio.Button(visible = False)


def create_and_run_job() -> bool:
	job_id = job_helper.suggest_job_id('ui')
	step_program = create_program()
	step_program = import_globals(step_program, job_store.get_step_keys(), [ facefusion, facefusion.processors.frame ])
	step_program = reduce_args(step_program, job_store.get_step_keys())
	step_args = vars(step_program.parse_args())

	return job_manager.create_job(job_id) and job_manager.add_step(job_id, step_args) and job_manager.submit_job(job_id) and job_runner.run_job(job_id, process_step)


def stop() -> Tuple[gradio.Button, gradio.Button]:
	process_manager.stop()
	return gradio.Button(visible = True), gradio.Button(visible = False)


def clear() -> Tuple[gradio.Image, gradio.Video]:
	while process_manager.is_processing():
		sleep(0.5)
	if facefusion.globals.target_path:
		clear_temp(facefusion.globals.target_path)
	return gradio.Image(value = None), gradio.Video(value = None)
