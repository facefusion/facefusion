from typing import Literal, Any, IO
import gradio

File = IO[Any]
Component = gradio.File or gradio.Image or gradio.Video or gradio.Slider
ComponentName = Literal\
[
	'source_image',
	'target_image',
	'target_video',
	'preview_frame_slider',
	'face_selector_mode_dropdown',
	'reference_face_position_gallery',
	'reference_face_distance_slider',
	'face_analyser_order_dropdown',
	'face_analyser_age_dropdown',
	'face_analyser_gender_dropdown',
	'face_detector_model_dropdown',
	'face_detector_size_dropdown',
	'face_detector_score_slider',
	'face_mask_types_checkbox_group',
	'face_mask_blur_slider',
	'face_mask_padding_top_slider',
	'face_mask_padding_bottom_slider',
	'face_mask_padding_left_slider',
	'face_mask_padding_right_slider',
	'face_mask_region_checkbox_group',
	'frame_processors_checkbox_group',
	'face_swapper_model_dropdown',
	'face_enhancer_model_dropdown',
	'face_enhancer_blend_slider',
	'frame_enhancer_model_dropdown',
	'frame_enhancer_blend_slider',
	'face_debugger_items_checkbox_group',
	'output_path_textbox',
	'benchmark_runs_checkbox_group',
	'benchmark_cycles_slider',
	'webcam_mode_radio',
	'webcam_resolution_dropdown',
	'webcam_fps_slider'
]
WebcamMode = Literal['inline', 'udp', 'v4l2']
StreamMode = Literal['udp', 'v4l2']
