import logging
from typing import List, Sequence

from facefusion.common_helper import create_float_range, create_int_range
from facefusion.typing import Angle, DownloadProvider, DownloadProviderSet, DownloadScope, ExecutionProvider, ExecutionProviderSet, FaceDetectorModel, FaceDetectorSet, FaceLandmarkerModel, FaceMaskRegion, FaceMaskRegionSet, FaceMaskType, FaceOccluderModel, FaceParserModel, FaceSelectorMode, FaceSelectorOrder, Gender, JobStatus, LogLevel, LogLevelSet, OutputAudioEncoder, OutputVideoEncoder, OutputVideoPreset, Race, Score, TempFrameFormat, UiWorkflow, VideoMemoryStrategy

face_detector_set : FaceDetectorSet =\
{
	'many': [ '640x640' ],
	'retinaface': [ '160x160', '320x320', '480x480', '512x512', '640x640' ],
	'scrfd': [ '160x160', '320x320', '480x480', '512x512', '640x640' ],
	'yoloface': [ '640x640' ]
}
face_detector_models : List[FaceDetectorModel] = list(face_detector_set.keys())
face_landmarker_models : List[FaceLandmarkerModel] = [ 'many', '2dfan4', 'peppa_wutz' ]
face_selector_modes : List[FaceSelectorMode] = [ 'many', 'one', 'reference' ]
face_selector_orders : List[FaceSelectorOrder] = [ 'left-right', 'right-left', 'top-bottom', 'bottom-top', 'small-large', 'large-small', 'best-worst', 'worst-best' ]
face_selector_genders : List[Gender] = [ 'female', 'male' ]
face_selector_races : List[Race] = [ 'white', 'black', 'latino', 'asian', 'indian', 'arabic' ]
face_occluder_models : List[FaceOccluderModel] = [ 'xseg_1', 'xseg_2' ]
face_parser_models : List[FaceParserModel] = [ 'bisenet_resnet_18', 'bisenet_resnet_34' ]
face_mask_types : List[FaceMaskType] = [ 'box', 'occlusion', 'region' ]
face_mask_region_set : FaceMaskRegionSet =\
{
	'skin': 1,
	'left-eyebrow': 2,
	'right-eyebrow': 3,
	'left-eye': 4,
	'right-eye': 5,
	'glasses': 6,
	'nose': 10,
	'mouth': 11,
	'upper-lip': 12,
	'lower-lip': 13
}
face_mask_regions : List[FaceMaskRegion] = list(face_mask_region_set.keys())
temp_frame_formats : List[TempFrameFormat] = [ 'bmp', 'jpg', 'png' ]
output_audio_encoders : List[OutputAudioEncoder] = [ 'aac', 'libmp3lame', 'libopus', 'libvorbis' ]
output_video_encoders : List[OutputVideoEncoder] = [ 'libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc', 'h264_amf', 'hevc_amf', 'h264_qsv', 'hevc_qsv', 'h264_videotoolbox', 'hevc_videotoolbox' ]
output_video_presets : List[OutputVideoPreset] = [ 'ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow' ]

image_template_sizes : List[float] = [ 0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 3.5, 4 ]
video_template_sizes : List[int] = [ 240, 360, 480, 540, 720, 1080, 1440, 2160, 4320 ]

execution_provider_set : ExecutionProviderSet =\
{
	'cpu': 'CPUExecutionProvider',
	'coreml': 'CoreMLExecutionProvider',
	'cuda': 'CUDAExecutionProvider',
	'directml': 'DmlExecutionProvider',
	'openvino': 'OpenVINOExecutionProvider',
	'rocm': 'ROCMExecutionProvider',
	'tensorrt': 'TensorrtExecutionProvider'
}
execution_providers : List[ExecutionProvider] = list(execution_provider_set.keys())
download_provider_set : DownloadProviderSet =\
{
	'github':
	{
		'url': 'https://github.com',
		'path': '/facefusion/facefusion-assets/releases/download/{base_name}/{file_name}'
	},
	'huggingface':
	{
		'url': 'https://huggingface.co',
		'path': '/facefusion/{base_name}/resolve/main/{file_name}'
	}
}
download_providers : List[DownloadProvider] = list(download_provider_set.keys())
download_scopes : List[DownloadScope] = [ 'lite', 'full' ]

video_memory_strategies : List[VideoMemoryStrategy] = [ 'strict', 'moderate', 'tolerant' ]

log_level_set : LogLevelSet =\
{
	'error': logging.ERROR,
	'warn': logging.WARNING,
	'info': logging.INFO,
	'debug': logging.DEBUG
}
log_levels : List[LogLevel] = list(log_level_set.keys())

ui_workflows : List[UiWorkflow] = [ 'instant_runner', 'job_runner', 'job_manager' ]
job_statuses : List[JobStatus] = [ 'drafted', 'queued', 'completed', 'failed' ]

execution_thread_count_range : Sequence[int] = create_int_range(1, 32, 1)
execution_queue_count_range : Sequence[int] = create_int_range(1, 4, 1)
system_memory_limit_range : Sequence[int] = create_int_range(0, 128, 4)
face_detector_angles : Sequence[Angle] = create_int_range(0, 270, 90)
face_detector_score_range : Sequence[Score] = create_float_range(0.0, 1.0, 0.05)
face_landmarker_score_range : Sequence[Score] = create_float_range(0.0, 1.0, 0.05)
face_mask_blur_range : Sequence[float] = create_float_range(0.0, 1.0, 0.05)
face_mask_padding_range : Sequence[int] = create_int_range(0, 100, 1)
face_selector_age_range : Sequence[int] = create_int_range(0, 100, 1)
reference_face_distance_range : Sequence[float] = create_float_range(0.0, 1.5, 0.05)
output_image_quality_range : Sequence[int] = create_int_range(0, 100, 1)
output_video_quality_range : Sequence[int] = create_int_range(0, 100, 1)
