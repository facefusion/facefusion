import gradio

import facefusion.globals
from facefusion.download import conditional_download
from facefusion.uis.components import about, frame_processors, frame_processors_options, execution, execution_thread_count, execution_queue_count, limit_resources, benchmark_options, benchmark


def pre_check() -> bool:
	if not facefusion.globals.skip_download:
		conditional_download('.assets/examples',
		[
			'https://github.com/facefusion/facefusion-assets/releases/download/examples/source.jpg',
			'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-240p.mp4',
			'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-360p.mp4',
			'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-540p.mp4',
			'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-720p.mp4',
			'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-1080p.mp4',
			'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-1440p.mp4',
			'https://github.com/facefusion/facefusion-assets/releases/download/examples/target-2160p.mp4'
		])
		return True
	return False


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
					frame_processors_options.render()
				with gradio.Blocks():
					execution.render()
					execution_thread_count.render()
					execution_queue_count.render()
				with gradio.Blocks():
					limit_resources.render()
				with gradio.Blocks():
					benchmark_options.render()
			with gradio.Column(scale = 5):
				with gradio.Blocks():
					benchmark.render()
	return layout


def listen() -> None:
	frame_processors.listen()
	frame_processors_options.listen()
	execution.listen()
	execution_thread_count.listen()
	execution_queue_count.listen()
	limit_resources.listen()
	benchmark.listen()


def run(ui : gradio.Blocks) -> None:
	ui.queue(concurrency_count = 2, api_open = False).launch(show_api = False)
