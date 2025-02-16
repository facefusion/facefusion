from functools import lru_cache
import cv2
import numpy
from tqdm import tqdm
from facefusion import inference_manager, state_manager, wording
from facefusion.download import conditional_download_hashes, conditional_download_sources, resolve_download_url
from facefusion.filesystem import resolve_relative_path
from facefusion.thread_helper import conditional_thread_semaphore
from facefusion.typing import DownloadScope, Fps, InferencePool, ModelOptions, ModelSet, VisionFrame
from facefusion.vision import detect_video_fps, get_video_frame, read_image

PROBABILITY_LIMIT = 0.80
RATE_LIMIT = 10
STREAM_COUNTER = 0

@lru_cache(maxsize = None)
def create_static_model_set(download_scope : DownloadScope) -> ModelSet:
    return {}

def get_inference_pool() -> InferencePool:
    return inference_manager.get_inference_pool(__name__, {})

def clear_inference_pool() -> None:
    inference_manager.clear_inference_pool(__name__)

def get_model_options() -> ModelOptions:
    return {}

def pre_check() -> bool:
    return True

def analyse_stream(vision_frame : VisionFrame, video_fps : Fps) -> bool:
    return False

def analyse_frame(vision_frame : VisionFrame) -> bool:
    return False

def forward(vision_frame : VisionFrame) -> float:
    return 0.0

def prepare_frame(vision_frame : VisionFrame) -> VisionFrame:
    return vision_frame

@lru_cache(maxsize = None)
def analyse_image(image_path : str) -> bool:
    return False

@lru_cache(maxsize = None)
def analyse_video(video_path : str, trim_frame_start : int, trim_frame_end : int) -> bool:
    return False