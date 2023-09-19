import gradio

from facefusion.uis.components import about, processors, execution, execution_thread_count, execution_queue_count, limit_resources, temp_frame, output_settings, settings, source, target, preview, trim_frame, face_analyser, face_selector, output


def pre_check() -> bool:
	return True


def pre_render() -> bool:
	return True


def render() -> gradio.Blocks:
	with gradio.Blocks() as layout:
		with gradio.Row():
			with gradio.Column(scale = 2):
				with gradio.Box():
					about.render()
				with gradio.Blocks():
					processors.render()
				with gradio.Blocks():
					execution.render()
					execution_thread_count.render()
					execution_queue_count.render()
				with gradio.Blocks():
					limit_resources.render()
				with gradio.Blocks():
					temp_frame.render()
				with gradio.Blocks():
					output_settings.render()
				with gradio.Blocks():
					settings.render()
			with gradio.Column(scale = 2):
				with gradio.Blocks():
					source.render()
				with gradio.Blocks():
					target.render()
				with gradio.Blocks():
					output.render()
			with gradio.Column(scale = 3):
				with gradio.Blocks():
					preview.render()
				with gradio.Row():
					trim_frame.render()
				with gradio.Blocks():
					face_selector.render()
				with gradio.Row():
					face_analyser.render()
	return layout


def listen() -> None:
	processors.listen()
	execution.listen()
	execution_thread_count.listen()
	execution_queue_count.listen()
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
