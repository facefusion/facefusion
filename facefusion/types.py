from collections import namedtuple
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, TypeAlias, TypedDict

import cv2
import numpy
from numpy.typing import NDArray
from onnxruntime import InferenceSession

Scale : TypeAlias = float
Score : TypeAlias = float
Angle : TypeAlias = int

Detection : TypeAlias = NDArray[Any]
Prediction : TypeAlias = NDArray[Any]

BoundingBox : TypeAlias = NDArray[Any]
FaceLandmark5 : TypeAlias = NDArray[Any]
FaceLandmark68 : TypeAlias = NDArray[Any]
FaceLandmarkSet = TypedDict('FaceLandmarkSet',
{
	'5' : FaceLandmark5, #type:ignore[valid-type]
	'5/68' : FaceLandmark5, #type:ignore[valid-type]
	'68' : FaceLandmark68, #type:ignore[valid-type]
	'68/5' : FaceLandmark68 #type:ignore[valid-type]
})
FaceScoreSet = TypedDict('FaceScoreSet',
{
	'detector' : Score,
	'landmarker' : Score
})
Embedding : TypeAlias = NDArray[numpy.float64]
Gender = Literal['female', 'male']
Age : TypeAlias = range
Race = Literal['white', 'black', 'latino', 'asian', 'indian', 'arabic']
Face = namedtuple('Face',
[
	'bounding_box',
	'score_set',
	'landmark_set',
	'angle',
	'embedding',
	'normed_embedding',
	'gender',
	'age',
	'race'
])
FaceSet : TypeAlias = Dict[str, List[Face]]
FaceStore = TypedDict('FaceStore',
{
	'static_faces' : FaceSet,
	'reference_faces' : FaceSet
})
VideoPoolSet : TypeAlias = Dict[str, cv2.VideoCapture]

VisionFrame : TypeAlias = NDArray[Any]
Mask : TypeAlias = NDArray[Any]
Points : TypeAlias = NDArray[Any]
Distance : TypeAlias = NDArray[Any]
Matrix : TypeAlias = NDArray[Any]
Anchors : TypeAlias = NDArray[Any]
Translation : TypeAlias = NDArray[Any]

AudioBuffer : TypeAlias = bytes
Audio : TypeAlias = NDArray[Any]
AudioChunk : TypeAlias = NDArray[Any]
AudioFrame : TypeAlias = NDArray[Any]
Spectrogram : TypeAlias = NDArray[Any]
Mel : TypeAlias = NDArray[Any]
MelFilterBank : TypeAlias = NDArray[Any]

Fps : TypeAlias = float
Duration : TypeAlias = float
Padding : TypeAlias = Tuple[int, int, int, int]
Orientation = Literal['landscape', 'portrait']
Resolution : TypeAlias = Tuple[int, int]

ProcessState = Literal['checking', 'processing', 'stopping', 'pending']
QueuePayload = TypedDict('QueuePayload',
{
	'frame_number' : int,
	'frame_path' : str
})
Args : TypeAlias = Dict[str, Any]
UpdateProgress : TypeAlias = Callable[[int], None]
ProcessFrames : TypeAlias = Callable[[List[str], List[QueuePayload], UpdateProgress], None]
ProcessStep : TypeAlias = Callable[[str, int, Args], bool]

Content : TypeAlias = Dict[str, Any]

Commands : TypeAlias = List[str]

WarpTemplate = Literal['arcface_112_v1', 'arcface_112_v2', 'arcface_128', 'dfl_whole_face', 'ffhq_512', 'mtcnn_512', 'styleganex_384']
WarpTemplateSet : TypeAlias = Dict[WarpTemplate, NDArray[Any]]
ProcessMode = Literal['output', 'preview', 'stream']

ErrorCode = Literal[0, 1, 2, 3, 4]
LogLevel = Literal['error', 'warn', 'info', 'debug']
LogLevelSet : TypeAlias = Dict[LogLevel, int]

TableHeaders = List[str]
TableContents = List[List[Any]]

FaceDetectorModel = Literal['many', 'retinaface', 'scrfd', 'yolo_face']
FaceLandmarkerModel = Literal['many', '2dfan4', 'peppa_wutz']
FaceDetectorSet : TypeAlias = Dict[FaceDetectorModel, List[str]]
FaceSelectorMode = Literal['many', 'one', 'reference']
FaceSelectorOrder = Literal['left-right', 'right-left', 'top-bottom', 'bottom-top', 'small-large', 'large-small', 'best-worst', 'worst-best']
FaceOccluderModel = Literal['xseg_1', 'xseg_2', 'xseg_3']
FaceParserModel = Literal['bisenet_resnet_18', 'bisenet_resnet_34']
FaceMaskType = Literal['box', 'occlusion', 'area', 'region']
FaceMaskArea = Literal['upper-face', 'lower-face', 'mouth']
FaceMaskRegion = Literal['skin', 'left-eyebrow', 'right-eyebrow', 'left-eye', 'right-eye', 'glasses', 'nose', 'mouth', 'upper-lip', 'lower-lip']
FaceMaskRegionSet : TypeAlias = Dict[FaceMaskRegion, int]
FaceMaskAreaSet : TypeAlias = Dict[FaceMaskArea, List[int]]

AudioFormat = Literal['flac', 'm4a', 'mp3', 'ogg', 'opus', 'wav']
ImageFormat = Literal['bmp', 'jpeg', 'png', 'tiff', 'webp']
VideoFormat = Literal['avi', 'm4v', 'mkv', 'mov', 'mp4', 'webm']
TempFrameFormat = Literal['bmp', 'jpeg', 'png', 'tiff']
AudioTypeSet : TypeAlias = Dict[AudioFormat, str]
ImageTypeSet : TypeAlias = Dict[ImageFormat, str]
VideoTypeSet : TypeAlias = Dict[VideoFormat, str]

AudioEncoder = Literal['flac', 'aac', 'libmp3lame', 'libopus', 'libvorbis', 'pcm_s16le', 'pcm_s32le']
VideoEncoder = Literal['libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc', 'h264_amf', 'hevc_amf', 'h264_qsv', 'hevc_qsv', 'h264_videotoolbox', 'hevc_videotoolbox', 'rawvideo']
EncoderSet = TypedDict('EncoderSet',
{
	'audio' : List[AudioEncoder],
	'video' : List[VideoEncoder]
})
VideoPreset = Literal['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow']

BenchmarkResolution = Literal['240p', '360p', '540p', '720p', '1080p', '1440p', '2160p']
BenchmarkSet : TypeAlias = Dict[BenchmarkResolution, str]
BenchmarkCycleSet = TypedDict('BenchmarkCycleSet',
{
	'target_path' : str,
	'cycle_count' : int,
	'average_run' : float,
	'fastest_run' : float,
	'slowest_run' : float,
	'relative_fps' : float
})

WebcamMode = Literal['inline', 'udp', 'v4l2']
StreamMode = Literal['udp', 'v4l2']

ModelOptions : TypeAlias = Dict[str, Any]
ModelSet : TypeAlias = Dict[str, ModelOptions]
ModelInitializer : TypeAlias = NDArray[Any]

ExecutionProvider = Literal['cpu', 'coreml', 'cuda', 'directml', 'openvino', 'rocm', 'tensorrt']
ExecutionProviderValue = Literal['CPUExecutionProvider', 'CoreMLExecutionProvider', 'CUDAExecutionProvider', 'DmlExecutionProvider', 'OpenVINOExecutionProvider', 'ROCMExecutionProvider', 'TensorrtExecutionProvider']
ExecutionProviderSet : TypeAlias = Dict[ExecutionProvider, ExecutionProviderValue]
InferenceSessionProvider : TypeAlias = Any
ValueAndUnit = TypedDict('ValueAndUnit',
{
	'value' : int,
	'unit' : str
})
ExecutionDeviceFramework = TypedDict('ExecutionDeviceFramework',
{
	'name' : str,
	'version' : str
})
ExecutionDeviceProduct = TypedDict('ExecutionDeviceProduct',
{
	'vendor' : str,
	'name' : str
})
ExecutionDeviceVideoMemory = TypedDict('ExecutionDeviceVideoMemory',
{
	'total' : Optional[ValueAndUnit],
	'free' : Optional[ValueAndUnit]
})
ExecutionDeviceTemperature = TypedDict('ExecutionDeviceTemperature',
{
	'gpu' : Optional[ValueAndUnit],
	'memory' : Optional[ValueAndUnit]
})
ExecutionDeviceUtilization = TypedDict('ExecutionDeviceUtilization',
{
	'gpu' : Optional[ValueAndUnit],
	'memory' : Optional[ValueAndUnit]
})
ExecutionDevice = TypedDict('ExecutionDevice',
{
	'driver_version' : str,
	'framework' : ExecutionDeviceFramework,
	'product' : ExecutionDeviceProduct,
	'video_memory' : ExecutionDeviceVideoMemory,
	'temperature': ExecutionDeviceTemperature,
	'utilization' : ExecutionDeviceUtilization
})

DownloadProvider = Literal['github', 'huggingface']
DownloadProviderValue = TypedDict('DownloadProviderValue',
{
	'urls' : List[str],
	'path' : str
})
DownloadProviderSet : TypeAlias = Dict[DownloadProvider, DownloadProviderValue]
DownloadScope = Literal['lite', 'full']
Download = TypedDict('Download',
{
	'url' : str,
	'path' : str
})
DownloadSet : TypeAlias = Dict[str, Download]

VideoMemoryStrategy = Literal['strict', 'moderate', 'tolerant']
AppContext = Literal['cli', 'ui']

InferencePool : TypeAlias = Dict[str, InferenceSession]
InferencePoolSet : TypeAlias = Dict[AppContext, Dict[str, InferencePool]]

UiWorkflow = Literal['instant_runner', 'job_runner', 'job_manager']

JobStore = TypedDict('JobStore',
{
	'job_keys' : List[str],
	'step_keys' : List[str]
})
JobOutputSet : TypeAlias = Dict[str, List[str]]
JobStatus = Literal['drafted', 'queued', 'completed', 'failed']
JobStepStatus = Literal['drafted', 'queued', 'started', 'completed', 'failed']
JobStep = TypedDict('JobStep',
{
	'args' : Args,
	'status' : JobStepStatus
})
Job = TypedDict('Job',
{
	'version' : str,
	'date_created' : str,
	'date_updated' : Optional[str],
	'steps' : List[JobStep]
})
JobSet : TypeAlias = Dict[str, Job]

StateKey = Literal\
[
	'command',
	'config_path',
	'temp_path',
	'jobs_path',
	'source_paths',
	'target_path',
	'output_path',
	'source_pattern',
	'target_pattern',
	'output_pattern',
	'download_providers',
	'download_scope',
	'benchmark_resolutions',
	'benchmark_cycle_count',
	'face_detector_model',
	'face_detector_size',
	'face_detector_angles',
	'face_detector_score',
	'face_landmarker_model',
	'face_landmarker_score',
	'face_selector_mode',
	'face_selector_order',
	'face_selector_gender',
	'face_selector_race',
	'face_selector_age_start',
	'face_selector_age_end',
	'reference_face_position',
	'reference_face_distance',
	'reference_frame_number',
	'face_occluder_model',
	'face_parser_model',
	'face_mask_types',
	'face_mask_areas',
	'face_mask_regions',
	'face_mask_blur',
	'face_mask_padding',
	'trim_frame_start',
	'trim_frame_end',
	'temp_frame_format',
	'keep_temp',
	'output_image_quality',
	'output_image_resolution',
	'output_audio_encoder',
	'output_audio_quality',
	'output_audio_volume',
	'output_video_encoder',
	'output_video_preset',
	'output_video_quality',
	'output_video_resolution',
	'output_video_fps',
	'processors',
	'open_browser',
	'ui_layouts',
	'ui_workflow',
	'execution_device_id',
	'execution_providers',
	'execution_thread_count',
	'execution_queue_count',
	'video_memory_strategy',
	'system_memory_limit',
	'log_level',
	'halt_on_error',
	'job_id',
	'job_status',
	'step_index'
]
State = TypedDict('State',
{
	'command' : str,
	'config_path' : str,
	'temp_path' : str,
	'jobs_path' : str,
	'source_paths' : List[str],
	'target_path' : str,
	'output_path' : str,
	'source_pattern' : str,
	'target_pattern' : str,
	'output_pattern' : str,
	'download_providers': List[DownloadProvider],
	'download_scope': DownloadScope,
	'benchmark_resolutions': List[BenchmarkResolution],
	'benchmark_cycle_count': int,
	'face_detector_model' : FaceDetectorModel,
	'face_detector_size' : str,
	'face_detector_angles' : List[Angle],
	'face_detector_score' : Score,
	'face_landmarker_model' : FaceLandmarkerModel,
	'face_landmarker_score' : Score,
	'face_selector_mode' : FaceSelectorMode,
	'face_selector_order' : FaceSelectorOrder,
	'face_selector_race' : Race,
	'face_selector_gender' : Gender,
	'face_selector_age_start' : int,
	'face_selector_age_end' : int,
	'reference_face_position' : int,
	'reference_face_distance' : float,
	'reference_frame_number' : int,
	'face_occluder_model' : FaceOccluderModel,
	'face_parser_model' : FaceParserModel,
	'face_mask_types' : List[FaceMaskType],
	'face_mask_areas' : List[FaceMaskArea],
	'face_mask_regions' : List[FaceMaskRegion],
	'face_mask_blur' : float,
	'face_mask_padding' : Padding,
	'trim_frame_start' : int,
	'trim_frame_end' : int,
	'temp_frame_format' : TempFrameFormat,
	'keep_temp' : bool,
	'output_image_quality' : int,
	'output_image_resolution' : str,
	'output_audio_encoder' : AudioEncoder,
	'output_audio_quality' : int,
	'output_audio_volume' : int,
	'output_video_encoder' : VideoEncoder,
	'output_video_preset' : VideoPreset,
	'output_video_quality' : int,
	'output_video_resolution' : str,
	'output_video_fps' : float,
	'processors' : List[str],
	'open_browser' : bool,
	'ui_layouts' : List[str],
	'ui_workflow' : UiWorkflow,
	'execution_device_id' : str,
	'execution_providers' : List[ExecutionProvider],
	'execution_thread_count' : int,
	'execution_queue_count' : int,
	'video_memory_strategy' : VideoMemoryStrategy,
	'system_memory_limit' : int,
	'log_level' : LogLevel,
	'halt_on_error' : bool,
	'job_id' : str,
	'job_status' : JobStatus,
	'step_index' : int
})
ApplyStateItem : TypeAlias = Callable[[Any, Any], None]
StateSet : TypeAlias = Dict[AppContext, State]

