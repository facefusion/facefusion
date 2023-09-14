from typing import Literal, Dict, Any
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
	'benchmark_runs_checkbox_group',
	'benchmark_cycles_slider',
	'webcam_mode_radio',
	'webcam_resolution_dropdown',
	'webcam_fps_slider'
]
WebcamMode = Literal[ 'inline', 'stream_udp', 'stream_v4l2' ]
StreamMode = Literal[ 'udp', 'v4l2' ]
Update = Dict[Any, Any]
