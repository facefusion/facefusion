from typing import Optional, List
import gradio

import facefusion.globals
from facefusion import wording
from facefusion.uis.typing import File
from facefusion.filesystem import are_images
from facefusion.uis.core import register_ui_component

SOURCE_FILE : Optional[gradio.File] = None
SOURCE_IMAGE : Optional[gradio.Image] = None


def render() -> None:
	global SOURCE_FILE
	global SOURCE_IMAGE

	are_source_images = are_images(facefusion.globals.source_paths)
	SOURCE_FILE = gradio.File(
		file_count = 'multiple',
		file_types =
		[
			'.png',
			'.jpg',
			'.webp'
		],
		label = wording.get('source_file_label'),
		value = facefusion.globals.source_paths if are_source_images else None
	)
	source_file_names = [ source_file_value['name'] for source_file_value in SOURCE_FILE.value ] if SOURCE_FILE.value else None
	SOURCE_IMAGE = gradio.Image(
		value = source_file_names[0] if are_source_images else None,
		visible = are_source_images,
		show_label = False
	)
	register_ui_component('source_image', SOURCE_IMAGE)


def listen() -> None:
	SOURCE_FILE.change(update, inputs = SOURCE_FILE, outputs = SOURCE_IMAGE)


def update(files : List[File]) -> gradio.Image:
	file_names = [ file.name for file in files ] if files else None
	if are_images(file_names):
		facefusion.globals.source_paths = file_names
		return gradio.Image(value = file_names[0], visible = True)
	facefusion.globals.source_paths = None
	return gradio.Image(value = None, visible = False)
