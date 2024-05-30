from typing import Any, Dict, Tuple, Optional
from gradio_rangeslider import RangeSlider

import facefusion.globals
from facefusion import wording
from facefusion.face_store import clear_static_faces
from facefusion.vision import count_video_frame_total
from facefusion.filesystem import is_video
from facefusion.uis.core import get_ui_components

TRIM_FRAME_RANGE_SLIDER : Optional[RangeSlider] = None


def render() -> None:
	global TRIM_FRAME_RANGE_SLIDER

	trim_frame_range_slider_args : Dict[str, Any] =\
	{
		'label': wording.get('uis.trim_frame_start_slider'),
		'minimum': 0,
		'step': 1,
		'visible': False
	}
	if is_video(facefusion.globals.target_path):
		video_frame_total = count_video_frame_total(facefusion.globals.target_path)
		trim_frame_range_slider_args['maximum'] = video_frame_total
		trim_frame_range_slider_args['value'] = (0, video_frame_total)
		trim_frame_range_slider_args['visible'] = True
	TRIM_FRAME_RANGE_SLIDER = RangeSlider(**trim_frame_range_slider_args)


def listen() -> None:
	TRIM_FRAME_RANGE_SLIDER.change(update_trim_frame, inputs = TRIM_FRAME_RANGE_SLIDER)
	for ui_component in get_ui_components(
	[
		'target_image',
		'target_video'
	]):
		for method in [ 'upload', 'change', 'clear' ]:
			getattr(ui_component, method)(remote_update, outputs = [ TRIM_FRAME_RANGE_SLIDER ])


def remote_update() -> RangeSlider:
	if is_video(facefusion.globals.target_path):
		video_frame_total = count_video_frame_total(facefusion.globals.target_path)
		facefusion.globals.trim_frame_start = None
		facefusion.globals.trim_frame_end = None
		return RangeSlider(value = (0, video_frame_total), maximum = video_frame_total, visible = True)
	return RangeSlider(visible = False)


def update_trim_frame(trim_frame : Tuple[float, float]) -> None:
	trim_frame_start = int(trim_frame[0])
	trim_frame_end = int(trim_frame[1])
	clear_static_faces()
	video_frame_total = count_video_frame_total(facefusion.globals.target_path)
	facefusion.globals.trim_frame_start = trim_frame_start if trim_frame_start > 0 else None
	facefusion.globals.trim_frame_end = trim_frame_end if trim_frame_end < video_frame_total else None
