import gradio

from facefusion.uis.components import about, processors, execution, limit_resources, temp_frame, output_settings, settings, source, target, preview, trim_frame, face_analyser, face_selector, output


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
				temp_frame.render()
				output_settings.render()
				settings.render()
			with gradio.Column(scale = 2):
				source.render()
				target.render()
				output.render()
			with gradio.Column(scale = 3):
				preview.render()
				trim_frame.render()
				face_selector.render()
				face_analyser.render()
	return layout


def listen() -> None:
	processors.listen()
	execution.listen()
	limit_resources.listen()
	temp_frame.listen()
	output_settings.listen()
	settings.listen()
	source.listen()
	target.listen()
	preview.listen()
	trim_frame.listen()
	face_selector.listen()
	face_analyser.listen()
	output.listen()


def run(ui : gradio.Blocks) -> None:
	ui.launch(show_api = False)
