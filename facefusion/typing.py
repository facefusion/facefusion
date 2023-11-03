from collections import namedtuple
from typing import Any, Literal, Callable, List, TypedDict, Dict
import numpy

Bbox = List[float]
Kps = List[float]
Embedding = List[float]
Face = namedtuple('Face', [ 'bbox', 'kps', 'score', 'embedding', 'normed_embedding', 'gender', 'age' ])
Frame = numpy.ndarray[Any, Any]
Matrix = numpy.ndarray[Any, Any]

Update_Process = Callable[[], None]
Process_Frames = Callable[[str, List[str], Update_Process], None]

Template = Literal[ 'arcface', 'ffhq' ]
ProcessMode = Literal[ 'output', 'preview', 'stream' ]
FaceSelectorMode = Literal[ 'reference', 'many' ]
FaceAnalyserDirection = Literal[ 'left-right', 'right-left', 'top-bottom', 'bottom-top', 'small-large', 'large-small' ]
FaceAnalyserAge = Literal[ 'child', 'teen', 'adult', 'senior' ]
FaceAnalyserGender = Literal[ 'male', 'female' ]
FaceDetectionModel = Literal[ 'retinaface', 'yunet' ]
FaceRecognitionModel = Literal[ 'arcface_inswapper', 'arcface_simswap' ]
TempFrameFormat = Literal[ 'jpg', 'png' ]
OutputVideoEncoder = Literal[ 'libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc' ]

ModelValue = Dict['str', Any]
OptionsWithModel = TypedDict('OptionsWithModel',
{
	'model' : ModelValue
})
