import random
from typing import Optional

import gradio

from facefusion import metadata, translator
from facefusion.locals import LOCALS


translator.load(LOCALS, __name__)

METADATA_BUTTON : Optional[gradio.Button] = None
ACTION_BUTTON : Optional[gradio.Button] = None


def render() -> None:
	global METADATA_BUTTON
	global ACTION_BUTTON

	action = random.choice(
	[
		{
			'wording': translator.get('about.become_a_member', __name__),
			'url': 'https://subscribe.facefusion.io'
		},
		{
			'wording': translator.get('about.join_our_community', __name__),
			'url': 'https://join.facefusion.io'
		},
		{
			'wording': translator.get('about.read_the_documentation', __name__),
			'url': 'https://docs.facefusion.io'
		}
	])

	METADATA_BUTTON = gradio.Button(
		value = metadata.get('name') + ' ' + metadata.get('version'),
		variant = 'primary',
		link = metadata.get('url')
	)
	ACTION_BUTTON = gradio.Button(
		value = action.get('wording'),
		link = action.get('url'),
		size = 'sm'
	)
