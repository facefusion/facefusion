import threading
from functools import lru_cache

import numpy
import opennsfw2
from PIL import Image
from keras import Model

from facefusion.typing import Frame

PREDICTOR = None
THREAD_LOCK : threading.Lock = threading.Lock()
MAX_PROBABILITY = 0.75
FRAME_INTERVAL = 25
STREAM_COUNTER = 0


def get_predictor() -> Model:
	global PREDICTOR

	with THREAD_LOCK:
		if PREDICTOR is None:
			PREDICTOR = opennsfw2.make_open_nsfw_model()
	return PREDICTOR


def clear_predictor() -> None:
	global PREDICTOR

	PREDICTOR = None


def predict_stream(frame : Frame) -> bool:
	global STREAM_COUNTER

	STREAM_COUNTER = STREAM_COUNTER + 1
	if STREAM_COUNTER % FRAME_INTERVAL == 0:
		return predict_frame(frame)
	return False


def predict_frame(frame : Frame) -> bool:
	image = Image.fromarray(frame)
	image = opennsfw2.preprocess_image(image, opennsfw2.Preprocessing.YAHOO)
	views = numpy.expand_dims(image, axis = 0)
	_, probability = get_predictor().predict(views)[0]
	return probability > MAX_PROBABILITY


@lru_cache(maxsize = None)
def predict_image(image_path : str) -> bool:
	return opennsfw2.predict_image(image_path) > MAX_PROBABILITY


@lru_cache(maxsize = None)
def predict_video(video_path : str) -> bool:
	_, probabilities = opennsfw2.predict_video_frames(video_path = video_path, frame_interval = FRAME_INTERVAL)
	return any(probability > MAX_PROBABILITY for probability in probabilities)
