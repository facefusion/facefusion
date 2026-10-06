from typing import List, cast

from starlette.datastructures import UploadFile

import facefusion.choices
from facefusion import ffmpeg
from facefusion.apis.asset_helper import detect_media_type_by_format
from facefusion.filesystem import get_file_format
from facefusion.types import AudioFormat, ImageFormat, VideoFormat
from facefusion.vision import unpack_resolution


def validate_subject(subject : str) -> bool:
	return subject in [ 'frame', 'face' ]


def validate_resolution(resolution : str) -> bool:
	resolution_min = 63
	resolution_max = 4097

	if resolution:
		frame_width, frame_height = unpack_resolution(resolution)

		return resolution_min < frame_width < resolution_max and resolution_min < frame_height < resolution_max

	return False


def validate_frame_index(frame_indexes : List[str]) -> bool:
	frame_min = 0
	frame_max = 101
	frame_total = len(frame_indexes)

	return frame_min < frame_total < frame_max


def validate_asset_files(upload_files : List[UploadFile]) -> bool:
	available_encoder_set = ffmpeg.get_static_available_encoder_set()

	for upload_file in upload_files:
		file_format = get_file_format(upload_file.filename)
		media_type = detect_media_type_by_format(file_format)

		if media_type == 'audio' and facefusion.choices.audio_set.get(cast(AudioFormat, file_format)) not in available_encoder_set.get('audio'):
			return False

		if media_type == 'image' and facefusion.choices.image_set.get(cast(ImageFormat, file_format)) not in available_encoder_set.get('image'):
			return False

		if media_type == 'video' and facefusion.choices.video_set.get(cast(VideoFormat, file_format)) not in available_encoder_set.get('video'):
			return False

		return media_type in [ 'audio', 'image', 'video' ]

	return True
