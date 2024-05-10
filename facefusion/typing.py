from typing import Any, Literal, Callable, List, Tuple, Dict, TypedDict
from collections import namedtuple
import numpy

BoundingBox = numpy.ndarray[Any, Any]
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
	'landmarks',
	'scores',
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

WarpTemplate = Literal['arcface_112_v1', 'arcface_112_v2', 'arcface_128_v2', 'ffhq_512']
WarpTemplateSet = Dict[WarpTemplate, numpy.ndarray[Any, Any]]
ProcessMode = Literal['output', 'preview', 'stream']

LogLevel = Literal['error', 'warn', 'info', 'debug']
VideoMemoryStrategy = Literal['strict', 'moderate', 'tolerant']
FaceSelectorMode = Literal['many', 'one', 'reference']
FaceAnalyserOrder = Literal['left-right', 'right-left', 'top-bottom', 'bottom-top', 'small-large', 'large-small', 'best-worst', 'worst-best']
FaceAnalyserAge = Literal['child', 'teen', 'adult', 'senior']
FaceAnalyserGender = Literal['female', 'male']
FaceDetectorModel = Literal['many', 'retinaface', 'scrfd', 'yoloface', 'yunet']
FaceDetectorTweak = Literal['low-luminance', 'high-luminance']
FaceRecognizerModel = Literal['arcface_blendswap', 'arcface_inswapper', 'arcface_simswap', 'arcface_uniface']
FaceMaskType = Literal['box', 'occlusion', 'region']
FaceMaskRegion = Literal['skin', 'left-eyebrow', 'right-eyebrow', 'left-eye', 'right-eye', 'glasses', 'nose', 'mouth', 'upper-lip', 'lower-lip']
TempFrameFormat = Literal['jpg', 'png', 'bmp']
OutputVideoEncoder = Literal['libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc', 'h264_amf', 'hevc_amf']
OutputVideoPreset = Literal['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow']

ModelValue = Dict[str, Any]
ModelSet = Dict[str, ModelValue]
OptionsWithModel = TypedDict('OptionsWithModel',
{
	'model' : ModelValue
})

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
