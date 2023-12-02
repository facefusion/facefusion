from typing import Any, IO, Optional, List
import gradio

import facefusion.globals
from facefusion import wording
from facefusion.utilities import is_image
from facefusion.uis.core import register_ui_component

SOURCE_FILE : Optional[gradio.File] = None
SOURCE_IMAGE : Optional[gradio.Image] = None


def render() -> None:
	global SOURCE_FILE
	global SOURCE_IMAGE

	is_source_image = all(map(is_image, facefusion.globals.source_paths))
	SOURCE_FILE = gradio.File(
		file_count = 'multiple',
		file_types =
		[
			'.png',
			'.jpg',
			'.webp'
		],
		label = wording.get('source_file_label'),
		value = facefusion.globals.source_paths if is_source_image else None
	)
	SOURCE_IMAGE = gradio.Image(
		file_count = 'multiple',
		value = [ source_file_value['name'] for source_file_value in SOURCE_FILE.value ][0] if is_source_image else None,
		visible = is_source_image,
		show_label = False
	)
	register_ui_component('source_image', SOURCE_IMAGE)


def listen() -> None:
	SOURCE_FILE.change(update, inputs = SOURCE_FILE, outputs = SOURCE_IMAGE)


def update(files : List[IO[Any]]) -> gradio.Image:
	is_source_image = all(map(is_image, [ file.name for file in files ]))
	if is_source_image:
		facefusion.globals.source_paths = [ file.name for file in files ] if is_source_image else None
		return gradio.Image(value = facefusion.globals.source_paths, visible = True)
	facefusion.globals.source_paths = None
	return gradio.Image(value = None, visible = False)
