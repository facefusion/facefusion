import multiprocessing
import gradio

from facefusion.uis.components import about, frame_processors, frame_processors_options, execution, execution_thread_count, webcam_options, source, webcam


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
				with gradio.Blocks():
					webcam_options.render()
				with gradio.Blocks():
					source.render()
			with gradio.Column(scale = 5):
				with gradio.Blocks():
					webcam.render()
	return layout


def listen() -> None:
	frame_processors.listen()
	frame_processors_options.listen()
	execution.listen()
	execution_thread_count.listen()
	source.listen()
	webcam.listen()


def run(ui : gradio.Blocks) -> None:
	concurrency_count = min(2, multiprocessing.cpu_count())
	ui.queue(concurrency_count = concurrency_count).launch(show_api = False, quiet = True)
