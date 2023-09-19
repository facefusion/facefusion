from typing import Optional
import gradio

from facefusion import metadata

ABOUT_HTML : Optional[gradio.HTML] = None


def render() -> None:
	global ABOUT_HTML

	ABOUT_HTML = gradio.HTML('<center><a href="' + metadata.get('url') + '">' + metadata.get('name') + ' ' + metadata.get('version') + '</a></center>')
