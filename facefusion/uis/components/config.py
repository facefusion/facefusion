from typing import Optional

import gradio

from facefusion import logger

CONFIG_SAVE_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	"""
	Render the config save button.
	"""
	global CONFIG_SAVE_BUTTON

	CONFIG_SAVE_BUTTON = gradio.Button(
		value = "Save Settings",
		variant = 'secondary',
		size = 'sm'
	)


def listen() -> None:
	"""
	Listen for the click event on the config save button.
	"""
	CONFIG_SAVE_BUTTON.click(fn = save_configuration)


def save_configuration() -> None:
	"""
	Save the current UI settings to the config file and provide feedback to the console.
	"""
	from facefusion.config import save_to_file

	try:
		save_to_file()
		success_message = "Settings saved successfully to facefusion.ini!"
		logger.info(success_message, __name__)
	except Exception as e:
		error_message = "Could not save settings to facefusion.ini."
		logger.error(f'{error_message} {e}', __name__)