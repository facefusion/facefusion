from typing import List, Optional

import gradio

import facefusion.choices
from facefusion import state_manager, wording
from facefusion.typing import DownloadProvider

DOWNLOAD_PROVIDERS_CHECKBOX_GROUP : Optional[gradio.CheckboxGroup] = None


def render() -> None:
	global DOWNLOAD_PROVIDERS_CHECKBOX_GROUP

	DOWNLOAD_PROVIDERS_CHECKBOX_GROUP = gradio.CheckboxGroup(
		label = wording.get('uis.download_providers_checkbox_group'),
		choices = facefusion.choices.download_providers,
		value = state_manager.get_item('download_providers')
	)


def listen() -> None:
	DOWNLOAD_PROVIDERS_CHECKBOX_GROUP.change(update_download_providers, inputs = DOWNLOAD_PROVIDERS_CHECKBOX_GROUP, outputs = DOWNLOAD_PROVIDERS_CHECKBOX_GROUP)


def update_download_providers(download_providers : List[DownloadProvider]) -> gradio.CheckboxGroup:
	download_providers = download_providers or facefusion.choices.download_providers
	state_manager.set_item('download_providers', download_providers)
	return gradio.CheckboxGroup(value = state_manager.get_item('download_providers'))
