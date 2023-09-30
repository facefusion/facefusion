from typing import List

from facefusion.typing import FaceRecognition, FaceAnalyserDirection, FaceAnalyserAge, FaceAnalyserGender, TempFrameFormat, OutputVideoEncoder

face_recognitions : List[FaceRecognition] = [ 'reference', 'many' ]
face_analyser_directions : List[FaceAnalyserDirection] = [ 'left-right', 'right-left', 'top-bottom', 'bottom-top', 'small-large', 'large-small' ]
face_analyser_ages : List[FaceAnalyserAge] = [ 'child', 'teen', 'adult', 'senior' ]
face_analyser_genders : List[FaceAnalyserGender] = [ 'male', 'female' ]
temp_frame_formats : List[TempFrameFormat] = [ 'jpg', 'png' ]
output_video_encoders : List[OutputVideoEncoder] = [ 'libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc' ]
