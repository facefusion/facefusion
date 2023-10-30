from typing import List

from facefusion.typing import FaceSelectorMode, FaceAnalyserDirection, FaceAnalyserAge, FaceAnalyserGender, TempFrameFormat, OutputVideoEncoder


face_analyser_directions : List[FaceAnalyserDirection] = [ 'left-right', 'right-left', 'top-bottom', 'bottom-top', 'small-large', 'large-small' ]
face_analyser_ages : List[FaceAnalyserAge] = [ 'child', 'teen', 'adult', 'senior' ]
face_analyser_genders : List[FaceAnalyserGender] = [ 'male', 'female' ]
face_detection_sizes : List[str] = [ '320x320', '480x480', '512x512', '640x640', '768x768', '1024x1024' ]
face_selector_modes : List[FaceSelectorMode] = [ 'reference', 'many' ]
temp_frame_formats : List[TempFrameFormat] = [ 'jpg', 'png' ]
output_video_encoders : List[OutputVideoEncoder] = [ 'libx264', 'libx265', 'libvpx-vp9', 'h264_nvenc', 'hevc_nvenc' ]
