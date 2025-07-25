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
		value = "Save Defaults",
		variant = 'secondary',
		size = 'sm'
	)


def listen() -> None:
	"""
	Listen for the click event on the config defaults button.
	"""
	CONFIG_SAVE_BUTTON.click(fn = save_defaults)


def save_defaults() -> None:
	"""
	Save the current UI settings as defaults to the config file and provide feedback to the console.
	"""
	from facefusion.config import save_defaults as save_defaults_to_file

	try:
		save_defaults_to_file()
		success_message = "Defaults saved successfully to facefusion.ini!"
		logger.info(success_message, __name__)
	except Exception as e:
		error_message = "Could not save defaults to facefusion.ini."
		logger.error(f'{error_message} {e}', __name__)