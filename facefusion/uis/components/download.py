from typing import List, Optional

import gradio

from facefusion import content_analyser, face_classifier, face_detector, face_landmarker, face_masker, face_recognizer, state_manager, voice_extractor, wording
from facefusion.choices import download_provider_set
from facefusion.filesystem import list_directory
from facefusion.processors.core import get_processors_modules
from facefusion.typing import DownloadProviderKey

DOWNLOAD_PROVIDERS_CHECKBOX_GROUP : Optional[gradio.CheckboxGroup] = None


def render() -> None:
	global DOWNLOAD_PROVIDERS_CHECKBOX_GROUP

	DOWNLOAD_PROVIDERS_CHECKBOX_GROUP = gradio.CheckboxGroup(
		label = wording.get('uis.download_providers_checkbox_group'),
		choices = list(download_provider_set.keys()),
		value = state_manager.get_item('download_providers')
	)


def listen() -> None:
	DOWNLOAD_PROVIDERS_CHECKBOX_GROUP.change(update_download_providers, inputs = DOWNLOAD_PROVIDERS_CHECKBOX_GROUP, outputs = DOWNLOAD_PROVIDERS_CHECKBOX_GROUP)


def update_download_providers(download_providers : List[DownloadProviderKey]) -> gradio.CheckboxGroup:
	common_modules =\
	[
		content_analyser,
		face_classifier,
		face_detector,
		face_landmarker,
		face_recognizer,
		face_masker,
		voice_extractor
	]
	available_processors = list_directory('facefusion/processors/modules')
	processor_modules = get_processors_modules(available_processors)

	for module in common_modules + processor_modules:
		if hasattr(module, 'create_static_model_set'):
			module.create_static_model_set.cache_clear()

	download_providers = download_providers or list(download_provider_set.keys())
	state_manager.set_item('download_providers', download_providers)
	return gradio.CheckboxGroup(value = state_manager.get_item('download_providers'))
