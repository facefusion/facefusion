from typing import Any, Literal, Callable, List, Tuple, Dict, TypedDict
from collections import namedtuple
import numpy

Bbox = numpy.ndarray[Any, Any]
Kps = numpy.ndarray[Any, Any]
Score = float
Embedding = numpy.ndarray[Any, Any]
Face = namedtuple('Face',
[
	'bbox',
	'kps',
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
Frame = numpy.ndarray[Any, Any]
Mask = numpy.ndarray[Any, Any]
Matrix = numpy.ndarray[Any, Any]
Padding = Tuple[int, int, int, int]

Update_Process = Callable[[], None]
Process_Frames = Callable[[List[str], List[str], Update_Process], None]
LogLevel = Literal['error',	'warn',	'info',	'debug']
Template = Literal['arcface_112_v1', 'arcface_112_v2', 'arcface_128_v2', 'ffhq_512']
ProcessMode = Literal['output', 'preview', 'stream']
FaceSelectorMode = Literal['reference', 'one', 'many']
FaceAnalyserOrder = Literal['left-right', 'right-left', 'top-bottom', 'bottom-top', 'small-large', 'large-small', 'best-worst', 'worst-best']
FaceAnalyserAge = Literal['child', 'teen', 'adult', 'senior']
FaceAnalyserGender = Literal['male', 'female']
FaceDetectorModel = Literal['retinaface', 'yunet']
FaceRecognizerModel = Literal['arcface_blendswap', 'arcface_inswapper', 'arcface_simswap']
FaceMaskType = Literal['box', 'occlusion', 'region']
FaceMaskRegion = Literal['skin', 'left-eyebrow', 'right-eyebrow', 'left-eye', 'right-eye', 'eye-glasses', 'nose', 'mouth', 'upper-lip', 'lower-lip']
TempFrameFormat = Literal['jpg', 'png']
OutputVideoEncoder = Literal['libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc']

ModelValue = Dict[str, Any]
ModelSet = Dict[str, ModelValue]
OptionsWithModel = TypedDict('OptionsWithModel',
{
	'model' : ModelValue
})
