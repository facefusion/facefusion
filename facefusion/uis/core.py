from typing import Dict, Optional, Any
import importlib
import sys
import cv2
import gradio

import facefusion.globals
from facefusion import metadata, wording
from facefusion.typing import Frame
from facefusion.uis.typing import Component, ComponentName

COMPONENTS: Dict[ComponentName, Component] = {}
UI_LAYOUT_METHODS =\
[
	'pre_check',
	'render',
	'listen'
]


def launch() -> None:
	with gradio.Blocks(theme = get_theme(), title = metadata.get('name') + ' ' + metadata.get('version')) as ui:
		for ui_layout in facefusion.globals.ui_layouts:
			ui_layout_module = load_ui_layout_module(ui_layout)
			ui_layout_module.pre_check()
			ui_layout_module.render()
			ui_layout_module.listen()
	ui.launch(show_api = False)


def load_ui_layout_module(ui_layout : str) -> Any:
	try:
		ui_layout_module = importlib.import_module('facefusion.uis.layouts.' + ui_layout)
		for method_name in UI_LAYOUT_METHODS:
			if not hasattr(ui_layout_module, method_name):
				raise NotImplementedError
	except ModuleNotFoundError:
		sys.exit(wording.get('ui_layout_not_loaded').format(ui_layout = ui_layout))
	except NotImplementedError:
		sys.exit(wording.get('ui_layout_not_implemented').format(ui_layout = ui_layout))
	return ui_layout_module


def get_theme() -> gradio.Theme:
	return gradio.themes.Soft(
		primary_hue = gradio.themes.colors.red,
		secondary_hue = gradio.themes.colors.gray,
		font = gradio.themes.GoogleFont('Inter')
	).set(
		background_fill_primary = '*neutral_50',
		block_label_text_size = '*text_sm',
		block_title_text_size = '*text_sm'
	)


def get_component(name: ComponentName) -> Optional[Component]:
	if name in COMPONENTS:
		return COMPONENTS[name]
	return None


def register_component(name: ComponentName, component: Component) -> None:
	COMPONENTS[name] = component


def normalize_frame(frame : Frame) -> Frame:
	return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
