<<<<<<< HEAD
from typing import Optional
=======
import random
from typing import Optional

>>>>>>> origin/master
import gradio

from facefusion import metadata, wording

<<<<<<< HEAD
ABOUT_BUTTON : Optional[gradio.HTML] = None
DONATE_BUTTON : Optional[gradio.HTML] = None


def render() -> None:
	global ABOUT_BUTTON
	global DONATE_BUTTON

	ABOUT_BUTTON = gradio.Button(
=======
METADATA_BUTTON : Optional[gradio.Button] = None
ACTION_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global METADATA_BUTTON
	global ACTION_BUTTON

	action = random.choice(
	[
		{
			'wording': wording.get('about.become_a_member'),
			'url': 'https://subscribe.facefusion.io'
		},
		{
			'wording': wording.get('about.join_our_community'),
			'url': 'https://join.facefusion.io'
		},
		{
			'wording': wording.get('about.read_the_documentation'),
			'url': 'https://docs.facefusion.io'
		}
	])

	METADATA_BUTTON = gradio.Button(
>>>>>>> origin/master
		value = metadata.get('name') + ' ' + metadata.get('version'),
		variant = 'primary',
		link = metadata.get('url')
	)
<<<<<<< HEAD
	DONATE_BUTTON = gradio.Button(
		value = wording.get('uis.donate_button'),
		link = 'https://donate.facefusion.io',
=======
	ACTION_BUTTON = gradio.Button(
		value = action.get('wording'),
		link = action.get('url'),
>>>>>>> origin/master
		size = 'sm'
	)
