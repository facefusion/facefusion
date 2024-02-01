from typing import Optional, List, Tuple
import gradio

import facefusion.globals
from facefusion import wording
from facefusion.uis.typing import File
from facefusion.common_helper import get_first_item
from facefusion.filesystem import are_audios, are_images, filter_audio_paths, filter_image_paths
from facefusion.uis.core import register_ui_component

SOURCE_FILE : Optional[gradio.File] = None
SOURCE_AUDIO : Optional[gradio.Audio] = None
SOURCE_IMAGE : Optional[gradio.Image] = None


def render() -> None:
	global SOURCE_FILE
	global SOURCE_AUDIO
	global SOURCE_IMAGE

	are_source_audios = are_audios(facefusion.globals.source_paths)
	are_source_images = are_images(facefusion.globals.source_paths)
	SOURCE_FILE = gradio.File(
		file_count = 'multiple',
		file_types =
		[
			'.mp3',
			'.wav',
			'.png',
			'.jpg',
			'.webp'
		],
		label = wording.get('uis.source_file'),
		value = facefusion.globals.source_paths if are_source_audios or are_source_images else None
	)
	source_file_names = [ source_file_value['name'] for source_file_value in SOURCE_FILE.value ] if SOURCE_FILE.value else None
	source_audio_path = get_first_item(filter_audio_paths(source_file_names))
	source_image_path = get_first_item(filter_image_paths(source_file_names))
	SOURCE_AUDIO = gradio.Audio(
		value = source_audio_path if are_source_audios else None,
		visible = are_source_audios,
		show_label = False
	)
	SOURCE_IMAGE = gradio.Image(
		value = source_image_path if are_source_images else None,
		visible = are_source_images,
		show_label = False
	)
	register_ui_component('source_audio', SOURCE_AUDIO)
	register_ui_component('source_image', SOURCE_IMAGE)


def listen() -> None:
	SOURCE_FILE.change(update, inputs = SOURCE_FILE, outputs = [ SOURCE_AUDIO, SOURCE_IMAGE ])


def update(files : List[File]) -> Tuple[gradio.Audio, gradio.Image]:
	file_names = [ file.name for file in files ] if files else None
	audio_path = get_first_item(filter_audio_paths(file_names))
	image_path = get_first_item(filter_image_paths(file_names))
	has_audio = bool(audio_path)
	has_image = bool(image_path)
	if audio_path or image_path:
		facefusion.globals.source_paths = file_names
		return gradio.Audio(value = audio_path, visible = has_audio), gradio.Image(value = image_path, visible = has_image)
	facefusion.globals.source_paths = None
	return gradio.Audio(value = None, visible = False), gradio.Image(value = None, visible = False)
