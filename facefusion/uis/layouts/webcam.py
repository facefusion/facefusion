import gradio

from facefusion.uis.components import about, processors, execution, source, webcam


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
			with gradio.Column(scale = 5):
				source.render()
				webcam.render()
	return layout


def listen() -> None:
	processors.listen()
	execution.listen()
	source.listen()
	webcam.listen()
