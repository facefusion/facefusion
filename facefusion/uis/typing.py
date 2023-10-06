from typing import Literal
import gradio

Component = gradio.File or gradio.Image or gradio.Video or gradio.Slider
ComponentName = Literal\
[
	'source_image',
	'target_image',
	'target_video',
	'preview_frame_slider',
	'face_recognition_dropdown',
	'reference_face_position_gallery',
	'reference_face_distance_slider',
	'face_analyser_direction_dropdown',
	'face_analyser_age_dropdown',
	'face_analyser_gender_dropdown',
	'frame_processors_checkbox_group',
	'face_swapper_model_dropdown',
	'face_enhancer_model_dropdown',
	'face_enhancer_blend_slider',
	'frame_enhancer_model_dropdown',
	'frame_enhancer_blend_slider',
	'output_path_textbox',
	'benchmark_runs_checkbox_group',
	'benchmark_cycles_slider',
	'player_url_textbox_label',
	'webcam_mode_radio',
	'webcam_resolution_dropdown',
	'webcam_fps_slider'
]
WebcamMode = Literal[ 'inline', 'udp', 'v4l2' ]
StreamMode = Literal[ 'udp', 'v4l2' ]
