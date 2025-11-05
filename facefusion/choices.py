import logging
from typing import List, Sequence, get_args

from facefusion.common_helper import create_float_range, create_int_range
from facefusion.types import Angle, AudioEncoder, AudioFormat, AudioTypeSet, BenchmarkMode, BenchmarkResolution, BenchmarkSet, DownloadProvider, DownloadProviderSet, DownloadScope, EncoderSet, ExecutionProvider, ExecutionProviderSet, FaceDetectorModel, FaceDetectorSet, FaceLandmarkerModel, FaceMaskArea, FaceMaskAreaSet, FaceMaskRegion, FaceMaskRegionSet, FaceMaskType, FaceOccluderModel, FaceParserModel, FaceSelectorMode, FaceSelectorOrder, Gender, ImageFormat, ImageTypeSet, JobStatus, LogLevel, LogLevelSet, Race, Score, TempFrameFormat, UiWorkflow, VideoEncoder, VideoFormat, VideoMemoryStrategy, VideoPreset, VideoTypeSet, VoiceExtractorModel

face_detector_set : FaceDetectorSet =\
{
	'many': [ '640x640' ],
	'retinaface': [ '160x160', '320x320', '480x480', '512x512', '640x640' ],
	'scrfd': [ '160x160', '320x320', '480x480', '512x512', '640x640' ],
	'yolo_face': [ '640x640' ],
	'yunet': [ '640x640' ]
}
face_detector_models : List[FaceDetectorModel] = list(get_args(FaceDetectorModel))
face_landmarker_models : List[FaceLandmarkerModel] = list(get_args(FaceLandmarkerModel))
face_selector_modes : List[FaceSelectorMode] = list(get_args(FaceSelectorMode))
face_selector_orders : List[FaceSelectorOrder] = list(get_args(FaceSelectorOrder))
face_selector_genders : List[Gender] = list(get_args(Gender))
face_selector_races : List[Race] = list(get_args(Race))
face_occluder_models : List[FaceOccluderModel] = list(get_args(FaceOccluderModel))
face_parser_models : List[FaceParserModel] = list(get_args(FaceParserModel))
face_mask_types : List[FaceMaskType] = list(get_args(FaceMaskType))
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
face_mask_areas : List[FaceMaskArea] = list(get_args(FaceMaskArea))
face_mask_regions : List[FaceMaskRegion] = list(get_args(FaceMaskRegion))

voice_extractor_models : List[VoiceExtractorModel] = list(get_args(VoiceExtractorModel))

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
	'mpeg': 'video/mpeg',
	'mov': 'video/quicktime',
	'mxf': 'application/mxf',
	'webm': 'video/webm',
	'wmv': 'video/x-ms-wmv'
}
audio_formats : List[AudioFormat] = list(get_args(AudioFormat))
image_formats : List[ImageFormat] = list(get_args(ImageFormat))
video_formats : List[VideoFormat] = list(get_args(VideoFormat))
temp_frame_formats : List[TempFrameFormat] = list(get_args(TempFrameFormat))

output_audio_encoders : List[AudioEncoder] = list(get_args(AudioEncoder))
output_video_encoders : List[VideoEncoder] = list(get_args(VideoEncoder))
output_encoder_set : EncoderSet =\
{
	'audio': output_audio_encoders,
	'video': output_video_encoders
}
output_video_presets : List[VideoPreset] = list(get_args(VideoPreset))

benchmark_modes : List[BenchmarkMode] = list(get_args(BenchmarkMode))
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
benchmark_resolutions : List[BenchmarkResolution] = list(get_args(BenchmarkResolution))

execution_provider_set : ExecutionProviderSet =\
{
	'cuda': 'CUDAExecutionProvider',
	'tensorrt': 'TensorrtExecutionProvider',
	'rocm': 'ROCMExecutionProvider',
	'migraphx': 'MIGraphXExecutionProvider',
	'coreml': 'CoreMLExecutionProvider',
	'openvino': 'OpenVINOExecutionProvider',
	'qnn': 'QNNExecutionProvider',
	'directml': 'DmlExecutionProvider',
	'cpu': 'CPUExecutionProvider'
}
execution_providers : List[ExecutionProvider] = list(get_args(ExecutionProvider))
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
download_providers : List[DownloadProvider] = list(get_args(DownloadProvider))
download_scopes : List[DownloadScope] = list(get_args(DownloadScope))

video_memory_strategies : List[VideoMemoryStrategy] = list(get_args(VideoMemoryStrategy))

log_level_set : LogLevelSet =\
{
	'error': logging.ERROR,
	'warn': logging.WARNING,
	'info': logging.INFO,
	'debug': logging.DEBUG
}
log_levels : List[LogLevel] = list(get_args(LogLevel))

job_statuses : List[JobStatus] = list(get_args(JobStatus))

benchmark_cycle_count_range : Sequence[int] = create_int_range(1, 10, 1)
execution_thread_count_range : Sequence[int] = create_int_range(1, 32, 1)
system_memory_limit_range : Sequence[int] = create_int_range(0, 128, 4)
face_detector_margin_range : Sequence[int] = create_int_range(0, 100, 1)
face_detector_angles : Sequence[Angle] = create_int_range(0, 270, 90)
face_detector_score_range : Sequence[Score] = create_float_range(0.0, 1.0, 0.05)
face_landmarker_score_range : Sequence[Score] = create_float_range(0.0, 1.0, 0.05)
face_mask_blur_range : Sequence[float] = create_float_range(0.0, 1.0, 0.05)
face_mask_padding_range : Sequence[int] = create_int_range(0, 100, 1)
face_selector_age_range : Sequence[int] = create_int_range(0, 100, 1)
reference_face_distance_range : Sequence[float] = create_float_range(0.0, 1.0, 0.05)
output_image_quality_range : Sequence[int] = create_int_range(0, 100, 1)
output_image_scale_range : Sequence[float] = create_float_range(0.25, 8.0, 0.25)
output_audio_quality_range : Sequence[int] = create_int_range(0, 100, 1)
output_audio_volume_range : Sequence[int] = create_int_range(0, 100, 1)
output_video_quality_range : Sequence[int] = create_int_range(0, 100, 1)
output_video_scale_range : Sequence[float] = create_float_range(0.25, 8.0, 0.25)
