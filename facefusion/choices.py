from typing import List

from facefusion.typing import FaceRecognition, FaceAnalyserDirection, FaceAnalyserAge, FaceAnalyserGender, TempFrameFormat, OutputVideoEncoder

face_recognition : List[FaceRecognition] = [ 'reference', 'many' ]
face_analyser_direction : List[FaceAnalyserDirection] = [ 'left-right', 'right-left', 'top-bottom', 'bottom-top', 'small-large', 'large-small' ]
face_analyser_age : List[FaceAnalyserAge] = [ 'child', 'teen', 'adult', 'senior' ]
face_analyser_gender : List[FaceAnalyserGender] = [ 'male', 'female' ]
temp_frame_format : List[TempFrameFormat] = [ 'jpg', 'png' ]
output_video_encoder : List[OutputVideoEncoder] = [ 'libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc' ]

