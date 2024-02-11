from typing import Any, Literal, Callable, List, Tuple, Dict, TypedDict
from collections import namedtuple
import numpy

BoundingBox = numpy.ndarray[Any, Any]
FaceLandmark5 = numpy.ndarray[Any, Any]
FaceLandmark68 = numpy.ndarray[Any, Any]
FaceLandmarkSet = TypedDict('FaceLandmarkSet',
{
	'5' : FaceLandmark5, # type: ignore[valid-type]
	'5/68' : FaceLandmark5, # type: ignore[valid-type]
	'68' : FaceLandmark68 # type: ignore[valid-type]
})
Score = float
Embedding = numpy.ndarray[Any, Any]
Face = namedtuple('Face',
[
	'bounding_box',
	'landmark',
	'score',
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
AudioFrame = numpy.ndarray[Any, Any]
Spectrogram = numpy.ndarray[Any, Any]

Fps = float
Padding = Tuple[int, int, int, int]
Resolution = Tuple[int, int]

QueuePayload = TypedDict('QueuePayload',
{
	'frame_number' : int,
	'frame_path' : str
})
Update_Process = Callable[[], None]
Process_Frames = Callable[[List[str], List[QueuePayload], Update_Process], None]

Template = Literal['arcface_112_v1', 'arcface_112_v2', 'arcface_128_v2', 'ffhq_512']
ProcessMode = Literal['output', 'preview', 'stream']

LogLevel = Literal['error', 'warn', 'info', 'debug']
VideoMemoryStrategy = Literal['strict', 'moderate', 'tolerant']
FaceSelectorMode = Literal['reference', 'one', 'many']
FaceAnalyserOrder = Literal['left-right', 'right-left', 'top-bottom', 'bottom-top', 'small-large', 'large-small', 'best-worst', 'worst-best']
FaceAnalyserAge = Literal['child', 'teen', 'adult', 'senior']
FaceAnalyserGender = Literal['female', 'male']
FaceDetectorModel = Literal['retinaface', 'yoloface', 'yunet']
FaceRecognizerModel = Literal['arcface_blendswap', 'arcface_inswapper', 'arcface_simswap', 'arcface_uniface']
FaceMaskType = Literal['box', 'occlusion', 'region']
FaceMaskRegion = Literal['skin', 'left-eyebrow', 'right-eyebrow', 'left-eye', 'right-eye', 'eye-glasses', 'nose', 'mouth', 'upper-lip', 'lower-lip']
TempFrameFormat = Literal['jpg', 'png', 'bmp']
OutputVideoEncoder = Literal['libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc']
OutputVideoPreset = Literal['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 'medium', 'slow', 'slower', 'veryslow']

ModelValue = Dict[str, Any]
ModelSet = Dict[str, ModelValue]
OptionsWithModel = TypedDict('OptionsWithModel',
{
	'model' : ModelValue
})
