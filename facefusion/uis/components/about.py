import random
from typing import Optional

import gradio

from facefusion import metadata, translator

METADATA_BUTTON : Optional[gradio.Button] = None
ACTION_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global METADATA_BUTTON
	global ACTION_BUTTON

	action = random.choice(
	[
		{
			'translator': translator.get('about.become_a_member', 'facefusion'),
			'url': 'https://subscribe.facefusion.io'
		},
		{
			'translator': translator.get('about.join_our_community'),
			'url': 'https://join.facefusion.io'
		},
		{
			'translator': translator.get('about.read_the_documentation'),
			'url': 'https://docs.facefusion.io'
		}
	])

	METADATA_BUTTON = gradio.Button(
		value = metadata.get('name') + ' ' + metadata.get('version'),
		variant = 'primary',
		link = metadata.get('url')
	)
	ACTION_BUTTON = gradio.Button(
		value = action.get('translator'),
		link = action.get('url'),
		size = 'sm'
	)
