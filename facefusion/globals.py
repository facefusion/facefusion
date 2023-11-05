from typing import List, Optional

from facefusion.typing import FaceSelectorMode, FaceAnalyserDirection, FaceAnalyserAge, FaceAnalyserGender, OutputVideoEncoder, FaceDetectionModel, FaceRecognitionModel, TempFrameFormat

# general
source_path : Optional[str] = None
target_path : Optional[str] = None
output_path : Optional[str] = None
# misc
skip_download : Optional[bool] = None
headless : Optional[bool] = None
# execution
execution_providers : List[str] = []
execution_thread_count : Optional[int] = None
execution_queue_count : Optional[int] = None
max_memory : Optional[int] = None
# face analyser
face_analyser_direction : Optional[FaceAnalyserDirection] = None
face_analyser_age : Optional[FaceAnalyserAge] = None
face_analyser_gender : Optional[FaceAnalyserGender] = None
face_detection_model : Optional[FaceDetectionModel] = None
face_detection_size : Optional[str] = None
face_detection_score : Optional[float] = None
face_recognition_model : Optional[FaceRecognitionModel] = None
# face selector
face_selector_mode : Optional[FaceSelectorMode] = None
reference_face_position : Optional[int] = None
reference_face_distance : Optional[float] = None
reference_frame_number : Optional[int] = None
# frame extraction
trim_frame_start : Optional[int] = None
trim_frame_end : Optional[int] = None
temp_frame_format : Optional[TempFrameFormat] = None
temp_frame_quality : Optional[int] = None
keep_temp : Optional[bool] = None
# output creation
output_image_quality : Optional[int] = None
output_video_encoder : Optional[OutputVideoEncoder] = None
output_video_quality : Optional[int] = None
keep_fps : Optional[bool] = None
skip_audio : Optional[bool] = None
# frame processors
frame_processors : List[str] = []
# uis
ui_layouts : List[str] = []
