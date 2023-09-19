from typing import List, Optional

from facefusion.typing import FaceRecognition, FaceAnalyserDirection, FaceAnalyserAge, FaceAnalyserGender, TempFrameFormat, OutputVideoEncoder

source_path : Optional[str] = None
target_path : Optional[str] = None
output_path : Optional[str] = None
headless : Optional[bool] = None
frame_processors : List[str] = []
ui_layouts : List[str] = []
keep_fps : Optional[bool] = None
keep_temp : Optional[bool] = None
skip_audio : Optional[bool] = None
face_recognition : Optional[FaceRecognition] = None
face_analyser_direction : Optional[FaceAnalyserDirection] = None
face_analyser_age : Optional[FaceAnalyserAge] = None
face_analyser_gender : Optional[FaceAnalyserGender] = None
reference_face_position : Optional[int] = None
reference_frame_number : Optional[int] = None
reference_face_distance : Optional[float] = None
trim_frame_start : Optional[int] = None
trim_frame_end : Optional[int] = None
temp_frame_format : Optional[TempFrameFormat] = None
temp_frame_quality : Optional[int] = None
output_image_quality : Optional[int] = None
output_video_encoder : Optional[OutputVideoEncoder] = None
output_video_quality : Optional[int] = None
max_memory : Optional[int] = None
execution_providers : List[str] = []
execution_thread_count : Optional[int] = None
execution_queue_count : Optional[int] = None
