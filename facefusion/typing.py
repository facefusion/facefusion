from typing import Any, Literal, Callable, List, Tuple, Dict, TypedDict, Optional, Sequence
from numpy.typing import NDArray
from cv2.typing import Size
from collections import namedtuple
import numpy

BoundingBox = NDArray[numpy.float32]
RotatedBoundingBox = Tuple[Sequence[float], Size, float]
FaceLandmark5 = numpy.ndarray[Any, Any]
FaceLandmark68 = numpy.ndarray[Any, Any]
FaceLandmarkSet = TypedDict('FaceLandmarkSet',
{
	'5' : FaceLandmark5, #type:ignore[valid-type]
	'5/68' : FaceLandmark5, #type:ignore[valid-type]
	'68' : FaceLandmark68, #type:ignore[valid-type]
	'68/5' : FaceLandmark68 #type:ignore[valid-type]
})
Score = float
FaceScoreSet = TypedDict('FaceScoreSet',
{
	'detector' : Score,
	'landmarker' : Score
})
Embedding = numpy.ndarray[Any, Any]
Face = namedtuple('Face',
[
	'bounding_box',
	'rotated_bounding_box',
	'landmark_set',
	'score_set',
	'embedding',
	'normed_embedding',
	'gender',
	'age'
])
FaceSet = Dict[str, List[Face]]
FaceStore = TypedDict('FaceStore',
{
	'static_faces' : FaceSet,
	'reference_faces': FaceSet
})

VisionFrame = numpy.ndarray[Any, Any]
Mask = numpy.ndarray[Any, Any]
Matrix = numpy.ndarray[Any, Any]
Translation = numpy.ndarray[Any, Any]

AudioBuffer = bytes
Audio = numpy.ndarray[Any, Any]
AudioChunk = numpy.ndarray[Any, Any]
AudioFrame = numpy.ndarray[Any, Any]
Spectrogram = numpy.ndarray[Any, Any]
MelFilterBank = numpy.ndarray[Any, Any]

Fps = float
Padding = Tuple[int, int, int, int]
Resolution = Tuple[int, int]

ProcessState = Literal['checking', 'processing', 'stopping', 'pending']
QueuePayload = TypedDict('QueuePayload',
{
	'frame_number' : int,
	'frame_path' : str
})
UpdateProgress = Callable[[int], None]
ProcessFrames = Callable[[List[str], List[QueuePayload], UpdateProgress], None]
ProcessStep = Callable[[Dict[str, Any]], bool]
Args = Dict[str, Any]

WarpTemplate = Literal['arcface_112_v1', 'arcface_112_v2', 'arcface_128_v2', 'ffhq_512']
WarpTemplateSet = Dict[WarpTemplate, numpy.ndarray[Any, Any]]
ProcessMode = Literal['output', 'preview', 'stream']

ErrorCode = Literal[0, 1, 2, 3, 4]
LogLevel = Literal['error', 'warn', 'info', 'debug']

TableHeaders = List[str]
TableContents = List[List[int | float | str]]

VideoMemoryStrategy = Literal['strict', 'moderate', 'tolerant']
FaceDetectorModel = Literal['many', 'retinaface', 'scrfd', 'yoloface', 'yunet']
FaceDetectorSet = Dict[FaceDetectorModel, List[str]]
FaceRecognizerModel = Literal['arcface_blendswap', 'arcface_ghost', 'arcface_inswapper', 'arcface_simswap', 'arcface_uniface']
FaceSelectorMode = Literal['many', 'one', 'reference']
FaceSelectorOrder = Literal['left-right', 'right-left', 'top-bottom', 'bottom-top', 'small-large', 'large-small', 'best-worst', 'worst-best']
FaceSelectorAge = Literal['child', 'teen', 'adult', 'senior']
FaceSelectorGender = Literal['female', 'male']
FaceMaskType = Literal['box', 'occlusion', 'region']
FaceMaskRegion = Literal['skin', 'left-eyebrow', 'right-eyebrow', 'left-eye', 'right-eye', 'glasses', 'nose', 'mouth', 'upper-lip', 'lower-lip']
TempFrameFormat = Literal['jpg', 'png', 'bmp']
OutputAudioEncoder = Literal['aac', 'libmp3lame', 'libopus', 'libvorbis']
OutputVideoEncoder = Literal['libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc', 'h264_amf', 'hevc_amf']
OutputVideoPreset = Literal['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow']

ModelValue = Dict[str, Any]
ModelSet = Dict[str, ModelValue]
OptionsWithModel = TypedDict('OptionsWithModel',
{
	'model' : ModelValue
})

ExecutionProviderKey = Literal['cpu', 'coreml', 'cuda', 'directml', 'openvino', 'rocm', 'tensorrt']
ExecutionProviderValue = Literal['CPUExecutionProvider', 'CoreMLExecutionProvider', 'CUDAExecutionProvider', 'DmlExecutionProvider', 'OpenVINOExecutionProvider', 'ROCMExecutionProvider', 'TensorrtExecutionProvider']
ExecutionProviderSet = Dict[ExecutionProviderKey, ExecutionProviderValue]
ValueAndUnit = TypedDict('ValueAndUnit',
{
	'value' : str,
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
	'total' : ValueAndUnit,
	'free' : ValueAndUnit
})
ExecutionDeviceUtilization = TypedDict('ExecutionDeviceUtilization',
{
	'gpu' : ValueAndUnit,
	'memory' : ValueAndUnit
})
ExecutionDevice = TypedDict('ExecutionDevice',
{
	'driver_version' : str,
	'framework' : ExecutionDeviceFramework,
	'product' : ExecutionDeviceProduct,
	'video_memory' : ExecutionDeviceVideoMemory,
	'utilization' : ExecutionDeviceUtilization
})

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
