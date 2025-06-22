import logging
from typing import List, Sequence

from facefusion.common_helper import create_float_range, create_int_range
from facefusion.types import Angle, AudioEncoder, AudioFormat, AudioTypeSet, BenchmarkResolution, BenchmarkSet, DownloadProvider, DownloadProviderSet, DownloadScope, EncoderSet, ExecutionProvider, ExecutionProviderSet, FaceDetectorModel, FaceDetectorSet, FaceLandmarkerModel, FaceMaskArea, FaceMaskAreaSet, FaceMaskRegion, FaceMaskRegionSet, FaceMaskType, FaceOccluderModel, FaceParserModel, FaceSelectorMode, FaceSelectorOrder, Gender, ImageFormat, ImageTypeSet, JobStatus, LogLevel, LogLevelSet, Race, Score, TempFrameFormat, UiWorkflow, VideoEncoder, VideoFormat, VideoMemoryStrategy, VideoPreset, VideoTypeSet, WebcamMode

face_detector_set : FaceDetectorSet =\
{
	'many': [ '640x640' ],
	'retinaface': [ '160x160', '320x320', '480x480', '512x512', '640x640' ],
	'scrfd': [ '160x160', '320x320', '480x480', '512x512', '640x640' ],
	'yolo_face': [ '640x640' ]
}
face_detector_models : List[FaceDetectorModel] = list(face_detector_set.keys())
face_landmarker_models : List[FaceLandmarkerModel] = [ 'many', '2dfan4', 'peppa_wutz' ]
face_selector_modes : List[FaceSelectorMode] = [ 'many', 'one', 'reference' ]
face_selector_orders : List[FaceSelectorOrder] = [ 'left-right', 'right-left', 'top-bottom', 'bottom-top', 'small-large', 'large-small', 'best-worst', 'worst-best' ]
face_selector_genders : List[Gender] = [ 'female', 'male' ]
face_selector_races : List[Race] = [ 'white', 'black', 'latino', 'asian', 'indian', 'arabic' ]
face_occluder_models : List[FaceOccluderModel] = [ 'xseg_1', 'xseg_2', 'xseg_3' ]
face_parser_models : List[FaceParserModel] = [ 'bisenet_resnet_18', 'bisenet_resnet_34' ]
face_mask_types : List[FaceMaskType] = [ 'box', 'occlusion', 'area', 'region' ]
face_mask_area_set : FaceMaskAreaSet =\
{
	'upper-face': [ 0, 1, 2, 31, 32, 33, 34, 35, 14, 15, 16, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17 ],
	'lower-face': [ 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 35, 34, 33, 32, 31 ],
	'mouth': [ 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67 ]
}
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
face_mask_areas : List[FaceMaskArea] = list(face_mask_area_set.keys())
face_mask_regions : List[FaceMaskRegion] = list(face_mask_region_set.keys())

audio_type_set : AudioTypeSet =\
{
	'flac': 'audio/flac',
	'm4a': 'audio/mp4',
	'mp3': 'audio/mpeg',
	'ogg': 'audio/ogg',
	'opus': 'audio/opus',
	'wav': 'audio/x-wav'
}
image_type_set : ImageTypeSet =\
{
	'bmp': 'image/bmp',
	'jpeg': 'image/jpeg',
	'png': 'image/png',
	'tiff': 'image/tiff',
	'webp': 'image/webp'
}
video_type_set : VideoTypeSet =\
{
	'avi': 'video/x-msvideo',
	'm4v': 'video/mp4',
	'mkv': 'video/x-matroska',
	'mp4': 'video/mp4',
	'mov': 'video/quicktime',
	'webm': 'video/webm'
}
audio_formats : List[AudioFormat] = list(audio_type_set.keys())
image_formats : List[ImageFormat] = list(image_type_set.keys())
video_formats : List[VideoFormat] = list(video_type_set.keys())
temp_frame_formats : List[TempFrameFormat] = [ 'bmp', 'jpeg', 'png', 'tiff' ]

output_encoder_set : EncoderSet =\
{
	'audio': [ 'flac', 'aac', 'libmp3lame', 'libopus', 'libvorbis', 'pcm_s16le', 'pcm_s32le' ],
	'video': [ 'libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc', 'h264_amf', 'hevc_amf', 'h264_qsv', 'hevc_qsv', 'h264_videotoolbox', 'hevc_videotoolbox', 'rawvideo' ]
}
output_audio_encoders : List[AudioEncoder] = output_encoder_set.get('audio')
output_video_encoders : List[VideoEncoder] = output_encoder_set.get('video')
output_video_presets : List[VideoPreset] = [ 'ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow' ]

image_template_sizes : List[float] = [ 0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 3.5, 4 ]
video_template_sizes : List[int] = [ 240, 360, 480, 540, 720, 1080, 1440, 2160, 4320 ]

benchmark_set : BenchmarkSet =\
{
	'240p': '.assets/examples/target-240p.mp4',
	'360p': '.assets/examples/target-360p.mp4',
	'540p': '.assets/examples/target-540p.mp4',
	'720p': '.assets/examples/target-720p.mp4',
	'1080p': '.assets/examples/target-1080p.mp4',
	'1440p': '.assets/examples/target-1440p.mp4',
	'2160p': '.assets/examples/target-2160p.mp4'
}
benchmark_resolutions : List[BenchmarkResolution] = list(benchmark_set.keys())

webcam_modes : List[WebcamMode] = [ 'inline', 'udp', 'v4l2' ]
webcam_resolutions : List[str] = [ '320x240', '640x480', '800x600', '1024x768', '1280x720', '1280x960', '1920x1080', '2560x1440', '3840x2160' ]

execution_provider_set : ExecutionProviderSet =\
{
	'cuda': 'CUDAExecutionProvider',
	'tensorrt': 'TensorrtExecutionProvider',
	'directml': 'DmlExecutionProvider',
	'rocm': 'ROCMExecutionProvider',
	'openvino': 'OpenVINOExecutionProvider',
	'coreml': 'CoreMLExecutionProvider',
	'cpu': 'CPUExecutionProvider'
}
execution_providers : List[ExecutionProvider] = list(execution_provider_set.keys())
download_provider_set : DownloadProviderSet =\
{
	'github':
	{
		'urls':
		[
			'https://github.com'
		],
		'path': '/facefusion/facefusion-assets/releases/download/{base_name}/{file_name}'
	},
	'huggingface':
	{
		'urls':
		[
			'https://huggingface.co',
			'https://hf-mirror.com'
		],
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

benchmark_cycle_count_range : Sequence[int] = create_int_range(1, 10, 1)
execution_thread_count_range : Sequence[int] = create_int_range(1, 32, 1)
execution_queue_count_range : Sequence[int] = create_int_range(1, 4, 1)
system_memory_limit_range : Sequence[int] = create_int_range(0, 128, 4)
face_detector_angles : Sequence[Angle] = create_int_range(0, 270, 90)
face_detector_score_range : Sequence[Score] = create_float_range(0.0, 1.0, 0.05)
face_landmarker_score_range : Sequence[Score] = create_float_range(0.0, 1.0, 0.05)
face_mask_blur_range : Sequence[float] = create_float_range(0.0, 1.0, 0.05)
face_mask_padding_range : Sequence[int] = create_int_range(0, 100, 1)
face_selector_age_range : Sequence[int] = create_int_range(0, 100, 1)
reference_face_distance_range : Sequence[float] = create_float_range(0.0, 1.0, 0.05)
output_image_quality_range : Sequence[int] = create_int_range(0, 100, 1)
output_audio_quality_range : Sequence[int] = create_int_range(0, 100, 1)
output_audio_volume_range : Sequence[int] = create_int_range(0, 100, 1)
output_video_quality_range : Sequence[int] = create_int_range(0, 100, 1)
