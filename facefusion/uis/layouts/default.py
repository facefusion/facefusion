<<<<<<< HEAD
import multiprocessing
import gradio

import facefusion.globals
from facefusion.uis.components import about, frame_processors, frame_processors_options, execution, execution_thread_count, execution_queue_count, memory, temp_frame, output_options, common_options, source, target, output, preview, trim_frame, face_analyser, face_selector, face_masker
=======
import gradio

from facefusion import state_manager
from facefusion.uis.components import about, age_modifier_options, common_options, deep_swapper_options, download, execution, execution_queue_count, execution_thread_count, expression_restorer_options, face_debugger_options, face_detector, face_editor_options, face_enhancer_options, face_landmarker, face_masker, face_selector, face_swapper_options, frame_colorizer_options, frame_enhancer_options, instant_runner, job_manager, job_runner, lip_syncer_options, memory, output, output_options, preview, processors, source, target, temp_frame, terminal, trim_frame, ui_workflow
>>>>>>> origin/master


def pre_check() -> bool:
	return True


<<<<<<< HEAD
def pre_render() -> bool:
	return True


def render() -> gradio.Blocks:
	with gradio.Blocks() as layout:
		with gradio.Row():
			with gradio.Column(scale = 2):
				with gradio.Blocks():
					about.render()
				with gradio.Blocks():
					frame_processors.render()
				with gradio.Blocks():
					frame_processors_options.render()
=======
def render() -> gradio.Blocks:
	with gradio.Blocks() as layout:
		with gradio.Row():
			with gradio.Column(scale = 4):
				with gradio.Blocks():
					about.render()
				with gradio.Blocks():
					processors.render()
				with gradio.Blocks():
					age_modifier_options.render()
				with gradio.Blocks():
					deep_swapper_options.render()
				with gradio.Blocks():
					expression_restorer_options.render()
				with gradio.Blocks():
					face_debugger_options.render()
				with gradio.Blocks():
					face_editor_options.render()
				with gradio.Blocks():
					face_enhancer_options.render()
				with gradio.Blocks():
					face_swapper_options.render()
				with gradio.Blocks():
					frame_colorizer_options.render()
				with gradio.Blocks():
					frame_enhancer_options.render()
				with gradio.Blocks():
					lip_syncer_options.render()
>>>>>>> origin/master
				with gradio.Blocks():
					execution.render()
					execution_thread_count.render()
					execution_queue_count.render()
				with gradio.Blocks():
<<<<<<< HEAD
=======
					download.render()
				with gradio.Blocks():
>>>>>>> origin/master
					memory.render()
				with gradio.Blocks():
					temp_frame.render()
				with gradio.Blocks():
					output_options.render()
<<<<<<< HEAD
			with gradio.Column(scale = 2):
=======
			with gradio.Column(scale = 4):
>>>>>>> origin/master
				with gradio.Blocks():
					source.render()
				with gradio.Blocks():
					target.render()
				with gradio.Blocks():
					output.render()
<<<<<<< HEAD
			with gradio.Column(scale = 3):
=======
				with gradio.Blocks():
					terminal.render()
				with gradio.Blocks():
					ui_workflow.render()
					instant_runner.render()
					job_runner.render()
					job_manager.render()
			with gradio.Column(scale = 7):
>>>>>>> origin/master
				with gradio.Blocks():
					preview.render()
				with gradio.Blocks():
					trim_frame.render()
				with gradio.Blocks():
					face_selector.render()
				with gradio.Blocks():
					face_masker.render()
				with gradio.Blocks():
<<<<<<< HEAD
					face_analyser.render()
=======
					face_detector.render()
				with gradio.Blocks():
					face_landmarker.render()
>>>>>>> origin/master
				with gradio.Blocks():
					common_options.render()
	return layout


def listen() -> None:
<<<<<<< HEAD
	frame_processors.listen()
	frame_processors_options.listen()
	execution.listen()
	execution_thread_count.listen()
	execution_queue_count.listen()
=======
	processors.listen()
	age_modifier_options.listen()
	deep_swapper_options.listen()
	expression_restorer_options.listen()
	face_debugger_options.listen()
	face_editor_options.listen()
	face_enhancer_options.listen()
	face_swapper_options.listen()
	frame_colorizer_options.listen()
	frame_enhancer_options.listen()
	lip_syncer_options.listen()
	execution.listen()
	execution_thread_count.listen()
	execution_queue_count.listen()
	download.listen()
>>>>>>> origin/master
	memory.listen()
	temp_frame.listen()
	output_options.listen()
	source.listen()
	target.listen()
	output.listen()
<<<<<<< HEAD
=======
	instant_runner.listen()
	job_runner.listen()
	job_manager.listen()
	terminal.listen()
>>>>>>> origin/master
	preview.listen()
	trim_frame.listen()
	face_selector.listen()
	face_masker.listen()
<<<<<<< HEAD
	face_analyser.listen()
=======
	face_detector.listen()
	face_landmarker.listen()
>>>>>>> origin/master
	common_options.listen()


def run(ui : gradio.Blocks) -> None:
<<<<<<< HEAD
	concurrency_count = min(8, multiprocessing.cpu_count())
	ui.queue(concurrency_count = concurrency_count).launch(show_api = False, quiet = True, inbrowser = facefusion.globals.open_browser)
=======
	ui.launch(favicon_path = 'facefusion.ico', inbrowser = state_manager.get_item('open_browser'))
>>>>>>> origin/master
