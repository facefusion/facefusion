from collections import namedtuple
from typing import Any, Literal, Callable, List, TypedDict, Dict, Tuple
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
Frame = numpy.ndarray[Any, Any]
Matrix = numpy.ndarray[Any, Any]
Padding = Tuple[float, float, float, float]

Update_Process = Callable[[], None]
Process_Frames = Callable[[str, List[str], Update_Process], None]

Template = Literal['arcface_v1', 'arcface_v2', 'ffhq']
ProcessMode = Literal['output', 'preview', 'stream']
FaceSelectorMode = Literal['reference', 'many']
FaceAnalyserOrder = Literal['left-right', 'right-left', 'top-bottom', 'bottom-top', 'small-large', 'large-small', 'best-worst', 'worst-best']
FaceAnalyserAge = Literal['child', 'teen', 'adult', 'senior']
FaceAnalyserGender = Literal['male', 'female']
FaceDetectorModel = Literal['retinaface', 'yunet']
FaceRecognizerModel = Literal['arcface_inswapper', 'arcface_simswap']
TempFrameFormat = Literal['jpg', 'png']
OutputVideoEncoder = Literal['libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc']

ModelValue = Dict[str, Any]
OptionsWithModel = TypedDict('OptionsWithModel',
{
	'model' : ModelValue
})
