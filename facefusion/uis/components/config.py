from typing import Optional

import gradio

from facefusion import logger, wording

CONFIG_SAVE_BUTTON : Optional[gradio.Button] = None
CONFIG_STATUS_TEXTBOX : Optional[gradio.Textbox] = None


def render() -> None:
	"""
	Render the config save button and status textbox.
	"""
	global CONFIG_SAVE_BUTTON
	global CONFIG_STATUS_TEXTBOX

	CONFIG_SAVE_BUTTON = gradio.Button(
		value = "Save Settings",
		variant = 'secondary',
		size = 'sm'
	)
	CONFIG_STATUS_TEXTBOX = gradio.Textbox(
		label = "Status",
		value = '',
		visible = False,
		interactive = False,
		elem_classes = [ 'feedback' ]
	)


def listen() -> None:
	"""
	Listen for the click event on the config save button.
	"""
	CONFIG_SAVE_BUTTON.click(fn = save_configuration, outputs = CONFIG_STATUS_TEXTBOX)


def save_configuration() -> gradio.Textbox:
	"""
	Save the current UI settings to the config file and provide feedback.
	"""
	from facefusion.config import save_to_file

	try:
		save_to_file()
		success_message = "Settings saved successfully to facefusion.ini!"
		logger.info(success_message, __name__)
		return gradio.Textbox(value = success_message, visible = True)
	except Exception as e:
		error_message = "Could not save settings to facefusion.ini."
		logger.error(f'{error_message} {e}', __name__)
		return gradio.Textbox(value = error_message, visible = True)