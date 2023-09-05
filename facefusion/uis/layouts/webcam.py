import gradio

from facefusion.uis.components import about, processors, execution, limit_resources, source, webcam


def pre_check() -> bool:
	return True


def pre_render() -> bool:
	return True


def render() -> gradio.Blocks:
	with gradio.Blocks() as layout:
		with gradio.Row():
			with gradio.Column(scale = 2):
				about.render()
				processors.render()
				execution.render()
				limit_resources.render()
				source.render()
			with gradio.Column(scale = 5):
				webcam.render()
	return layout


def listen() -> None:
	processors.listen()
	execution.listen()
	limit_resources.listen()
	source.listen()
	webcam.listen()


def run(ui : gradio.Blocks) -> None:
	ui.queue(concurrency_count = 2, api_open = False)
	ui.launch(show_api = False)
