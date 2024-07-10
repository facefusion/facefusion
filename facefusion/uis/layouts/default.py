import gradio

from facefusion import state_manager
from facefusion.uis.components import about, common_options, execution, execution_queue_count, execution_thread_count, face_analyser, face_masker, face_selector, frame_processors, frame_processors_options, instant_runner, job_manager, job_runner, memory, output, output_options, preview, source, target, temp_frame, trim_frame, ui_workflow


def pre_check() -> bool:
	return True


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
				with gradio.Blocks():
					execution.render()
					execution_thread_count.render()
					execution_queue_count.render()
				with gradio.Blocks():
					memory.render()
				with gradio.Blocks():
					temp_frame.render()
				with gradio.Blocks():
					output_options.render()
			with gradio.Column(scale = 2):
				with gradio.Blocks():
					source.render()
				with gradio.Blocks():
					target.render()
				with gradio.Blocks():
					output.render()
					ui_workflow.render()
					instant_runner.render()
					job_runner.render()
					job_manager.render()
			with gradio.Column(scale = 3):
				with gradio.Blocks():
					preview.render()
				with gradio.Blocks():
					trim_frame.render()
				with gradio.Blocks():
					face_selector.render()
				with gradio.Blocks():
					face_masker.render()
				with gradio.Blocks():
					face_analyser.render()
				with gradio.Blocks():
					common_options.render()
	return layout


def listen() -> None:
	frame_processors.listen()
	frame_processors_options.listen()
	execution.listen()
	execution_thread_count.listen()
	execution_queue_count.listen()
	memory.listen()
	temp_frame.listen()
	output_options.listen()
	source.listen()
	target.listen()
	output.listen()
	ui_workflow.listen()
	instant_runner.listen()
	job_runner.listen()
	job_manager.listen()
	preview.listen()
	trim_frame.listen()
	face_selector.listen()
	face_masker.listen()
	face_analyser.listen()
	common_options.listen()


def run(ui : gradio.Blocks) -> None:
	ui.launch(show_api = False, inbrowser = state_manager.get_item('open_browser'))
