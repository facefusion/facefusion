<<<<<<< HEAD
import multiprocessing
import gradio

import facefusion.globals
from facefusion.uis.components import about, frame_processors, frame_processors_options, execution, execution_thread_count, webcam_options, source, webcam
=======
import gradio

from facefusion import state_manager
from facefusion.uis.components import about, age_modifier_options, deep_swapper_options, download, execution, execution_thread_count, expression_restorer_options, face_debugger_options, face_editor_options, face_enhancer_options, face_swapper_options, frame_colorizer_options, frame_enhancer_options, lip_syncer_options, processors, source, webcam, webcam_options
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
				with gradio.Blocks():
<<<<<<< HEAD
					webcam_options.render()
				with gradio.Blocks():
					source.render()
			with gradio.Column(scale = 5):
=======
					download.render()
				with gradio.Blocks():
					webcam_options.render()
				with gradio.Blocks():
					source.render()
			with gradio.Column(scale = 11):
>>>>>>> origin/master
				with gradio.Blocks():
					webcam.render()
	return layout


def listen() -> None:
<<<<<<< HEAD
	frame_processors.listen()
	frame_processors_options.listen()
=======
	processors.listen()
	age_modifier_options.listen()
	deep_swapper_options.listen()
	expression_restorer_options.listen()
	download.listen()
	face_debugger_options.listen()
	face_editor_options.listen()
	face_enhancer_options.listen()
	face_swapper_options.listen()
	frame_colorizer_options.listen()
	frame_enhancer_options.listen()
	lip_syncer_options.listen()
>>>>>>> origin/master
	execution.listen()
	execution_thread_count.listen()
	source.listen()
	webcam.listen()


def run(ui : gradio.Blocks) -> None:
<<<<<<< HEAD
	concurrency_count = min(2, multiprocessing.cpu_count())
	ui.queue(concurrency_count = concurrency_count).launch(show_api = False, quiet = True, inbrowser = facefusion.globals.open_browser)
=======
	ui.launch(favicon_path = 'facefusion.ico', inbrowser = state_manager.get_item('open_browser'))
>>>>>>> origin/master
