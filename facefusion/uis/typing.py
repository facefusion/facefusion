from typing import Any, IO, Literal

import gradio

File = IO[Any]
Component = gradio.File or gradio.Image or gradio.Video or gradio.Slider
ComponentName = Literal\
[
	'benchmark_cycles_slider',
	'benchmark_runs_checkbox_group',
	'face_debugger_items_checkbox_group',
	'face_detector_angles_checkbox_group',
	'face_detector_model_dropdown',
	'face_detector_score_slider',
	'face_detector_size_dropdown',
	'face_enhancer_blend_slider',
	'face_enhancer_model_dropdown',
	'face_landmarker_score_slider',
	'face_mask_blur_slider',
	'face_mask_padding_bottom_slider',
	'face_mask_padding_left_slider',
	'face_mask_padding_right_slider',
	'face_mask_padding_top_slider',
	'face_mask_region_checkbox_group',
	'face_mask_types_checkbox_group',
	'face_selector_age_dropdown',
	'face_selector_gender_dropdown',
	'face_selector_mode_dropdown',
	'face_selector_order_dropdown',
	'face_swapper_model_dropdown',
	'face_swapper_pixel_boost_dropdown',
	'frame_colorizer_blend_slider',
	'frame_colorizer_model_dropdown',
	'frame_colorizer_size_dropdown',
	'frame_enhancer_blend_slider',
	'frame_enhancer_model_dropdown',
	'frame_processors_checkbox_group',
	'instant_runner_group',
	'job_runner_group',
	'job_manager_group',
	'lip_syncer_model_dropdown',
	'output_image',
	'output_video',
	'output_video_fps_slider',
	'preview_frame_slider',
	'reference_face_distance_slider',
	'reference_face_position_gallery',
	'source_audio',
	'source_image',
	'target_image',
	'target_video',
	'webcam_fps_slider',
	'webcam_mode_radio',
	'webcam_resolution_dropdown'
]

WebcamMode = Literal['inline', 'udp', 'v4l2']
StreamMode = Literal['udp', 'v4l2']
