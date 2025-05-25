from typing import List, Optional

import gradio

import testingss.choices
from testingss import content_analyser, face_classifier, face_detector, face_landmarker, face_masker, face_recognizer, state_manager, voice_extractor, wording
from testingss.filesystem import get_file_name, resolve_file_paths
from testingss.processors.core import get_processors_modules
from testingss.types import DownloadProvider

DOWNLOAD_PROVIDERS_CHECKBOX_GROUP : Optional[gradio.CheckboxGroup] = None


def render() -> None:
	global DOWNLOAD_PROVIDERS_CHECKBOX_GROUP

	DOWNLOAD_PROVIDERS_CHECKBOX_GROUP = gradio.CheckboxGroup(
		label = wording.get('uis.download_providers_checkbox_group'),
		choices = testingss.choices.download_providers,
		value = state_manager.get_item('download_providers')
	)


def listen() -> None:
	DOWNLOAD_PROVIDERS_CHECKBOX_GROUP.change(update_download_providers, inputs = DOWNLOAD_PROVIDERS_CHECKBOX_GROUP, outputs = DOWNLOAD_PROVIDERS_CHECKBOX_GROUP)


def update_download_providers(download_providers : List[DownloadProvider]) -> gradio.CheckboxGroup:
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
	available_processors = [ get_file_name(file_path) for file_path in resolve_file_paths('testingss/processors/modules') ]
	processor_modules = get_processors_modules(available_processors)

	for module in common_modules + processor_modules:
		if hasattr(module, 'create_static_model_set'):
			module.create_static_model_set.cache_clear()

	download_providers = download_providers or testingss.choices.download_providers
	state_manager.set_item('download_providers', download_providers)
	return gradio.CheckboxGroup(value = state_manager.get_item('download_providers'))
