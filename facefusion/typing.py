from typing import Any, Literal
from insightface.app.common import Face
import numpy

Face = Face
Frame = numpy.ndarray[Any, Any]

FaceRecognition = Literal[ 'reference', 'many' ]
FaceAnalyserDirection = Literal[ 'left-right', 'right-left', 'top-bottom', 'bottom-top', 'small-large', 'large-small' ]
FaceAnalyserAge = Literal[ 'child', 'teen', 'adult', 'senior' ]
FaceAnalyserGender = Literal[ 'male', 'female' ]
TempFrameFormat = Literal[ 'jpg', 'png' ]
OutputVideoEncoder = Literal[ 'libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc' ]
