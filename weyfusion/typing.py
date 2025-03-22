from collections import namedtuple
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, TypedDict

import numpy
from numpy.typing import NDArray
from onnxruntime import InferenceSession

Scale = float
Score = float
Angle = int

Detection = NDArray[Any]
Prediction = NDArray[Any]

BoundingBox = NDArray[Any]
FaceLandmark5 = NDArray[Any]
FaceLandmark68 = NDArray[Any]
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
Embedding = NDArray[numpy.float64]
Gender = Literal['female', 'male']
Age = range
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
FaceSet = Dict[str, List[Face]]
FaceStore = TypedDict('FaceStore',
{
	'static_faces' : FaceSet,
	'reference_faces' : FaceSet
})

VisionFrame = NDArray[Any]
Mask = NDArray[Any]
Points = NDArray[Any]
Distance = NDArray[Any]
Matrix = NDArray[Any]
Anchors = NDArray[Any]
Translation = NDArray[Any]

AudioBuffer = bytes
Audio = NDArray[Any]
AudioChunk = NDArray[Any]
AudioFrame = NDArray[Any]
Spectrogram = NDArray[Any]
Mel = NDArray[Any]
MelFilterBank = NDArray[Any]

Fps = float
Duration = float
Padding = Tuple[int, int, int, int]
Orientation = Literal['landscape', 'portrait']
Resolution = Tuple[int, int]

ProcessState = Literal['checking', 'processing', 'stopping', 'pending']
QueuePayload = TypedDict('QueuePayload',
{
	'frame_number' : int,
	'frame_path' : str
})
Args = Dict[str, Any]
UpdateProgress = Callable[[int], None]
ProcessFrames = Callable[[List[str], List[QueuePayload], UpdateProgress], None]
ProcessStep = Callable[[str, int, Args], bool]

Content = Dict[str, Any]

WarpTemplate = Literal['arcface_112_v1', 'arcface_112_v2', 'arcface_128_v2', 'dfl_whole_face', 'ffhq_512', 'mtcnn_512', 'styleganex_384']
WarpTemplateSet = Dict[WarpTemplate, NDArray[Any]]
ProcessMode = Literal['output', 'preview', 'stream']

ErrorCode = Literal[0, 1, 2, 3, 4]
LogLevel = Literal['error', 'warn', 'info', 'debug']
LogLevelSet = Dict[LogLevel, int]

TableHeaders = List[str]
TableContents = List[List[Any]]

FaceDetectorModel = Literal['many', 'retinaface', 'scrfd', 'yoloface']
FaceLandmarkerModel = Literal['many', '2dfan4', 'peppa_wutz']
FaceDetectorSet = Dict[FaceDetectorModel, List[str]]
FaceSelectorMode = Literal['many', 'one', 'reference']
FaceSelectorOrder = Literal['left-right', 'right-left', 'top-bottom', 'bottom-top', 'small-large', 'large-small', 'best-worst', 'worst-best']
FaceOccluderModel = Literal['xseg_1', 'xseg_2']
FaceParserModel = Literal['bisenet_resnet_18', 'bisenet_resnet_34']
FaceMaskType = Literal['box', 'occlusion', 'region']
FaceMaskRegion = Literal['skin', 'left-eyebrow', 'right-eyebrow', 'left-eye', 'right-eye', 'glasses', 'nose', 'mouth', 'upper-lip', 'lower-lip']
FaceMaskRegionSet = Dict[FaceMaskRegion, int]
TempFrameFormat = Literal['bmp', 'jpg', 'png']
OutputAudioEncoder = Literal['aac', 'libmp3lame', 'libopus', 'libvorbis']
OutputVideoEncoder = Literal['libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc', 'h264_amf', 'hevc_amf','h264_qsv', 'hevc_qsv', 'h264_videotoolbox', 'hevc_videotoolbox']
OutputVideoPreset = Literal['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow']

ModelOptions = Dict[str, Any]
ModelSet = Dict[str, ModelOptions]
ModelInitializer = NDArray[Any]

ExecutionProvider = Literal['cpu', 'coreml', 'cuda', 'directml', 'openvino', 'rocm', 'tensorrt']
ExecutionProviderValue = Literal['CPUExecutionProvider', 'CoreMLExecutionProvider', 'CUDAExecutionProvider', 'DmlExecutionProvider', 'OpenVINOExecutionProvider', 'ROCMExecutionProvider', 'TensorrtExecutionProvider']
ExecutionProviderSet = Dict[ExecutionProvider, ExecutionProviderValue]
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
	'url' : str,
	'path' : str
})
DownloadProviderSet = Dict[DownloadProvider, DownloadProviderValue]
DownloadScope = Literal['lite', 'full']
Download = TypedDict('Download',
{
	'url' : str,
	'path' : str
})
DownloadSet = Dict[str, Download]

VideoMemoryStrategy = Literal['strict', 'moderate', 'tolerant']

File = TypedDict('File',
{
	'name' : str,
	'extension' : str,
	'path': str
})

AppContext = Literal['cli', 'ui']

InferencePool = Dict[str, InferenceSession]
InferencePoolSet = Dict[AppContext, Dict[str, InferencePool]]

UiWorkflow = Literal['instant_runner', 'job_runner', 'job_manager']

JobStore = TypedDict('JobStore',
{
	'job_keys' : List[str],
	'step_keys' : List[str]
})
JobOutputSet = Dict[str, List[str]]
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
JobSet = Dict[str, Job]

ApplyStateItem = Callable[[Any, Any], None]
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
	'face_mask_blur',
	'face_mask_padding',
	'face_mask_regions',
	'trim_frame_start',
	'trim_frame_end',
	'temp_frame_format',
	'keep_temp',
	'output_image_quality',
	'output_image_resolution',
	'output_audio_encoder',
	'output_video_encoder',
	'output_video_preset',
	'output_video_quality',
	'output_video_resolution',
	'output_video_fps',
	'skip_audio',
	'processors',
	'open_browser',
	'ui_layouts',
	'ui_workflow',
	'execution_device_id',
	'execution_providers',
	'execution_thread_count',
	'execution_queue_count',
	'download_providers',
	'download_scope',
	'video_memory_strategy',
	'system_memory_limit',
	'log_level',
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
	'face_mask_blur' : float,
	'face_mask_padding' : Padding,
	'face_mask_regions' : List[FaceMaskRegion],
	'trim_frame_start' : int,
	'trim_frame_end' : int,
	'temp_frame_format' : TempFrameFormat,
	'keep_temp' : bool,
	'output_image_quality' : int,
	'output_image_resolution' : str,
	'output_audio_encoder' : OutputAudioEncoder,
	'output_video_encoder' : OutputVideoEncoder,
	'output_video_preset' : OutputVideoPreset,
	'output_video_quality' : int,
	'output_video_resolution' : str,
	'output_video_fps' : float,
	'skip_audio' : bool,
	'processors' : List[str],
	'open_browser' : bool,
	'ui_layouts' : List[str],
	'ui_workflow' : UiWorkflow,
	'execution_device_id' : str,
	'execution_providers' : List[ExecutionProvider],
	'execution_thread_count' : int,
	'execution_queue_count' : int,
	'download_providers' : List[DownloadProvider],
	'download_scope' : DownloadScope,
	'video_memory_strategy' : VideoMemoryStrategy,
	'system_memory_limit' : int,
	'log_level' : LogLevel,
	'job_id' : str,
	'job_status' : JobStatus,
	'step_index' : int
})
StateSet = Dict[AppContext, State]
