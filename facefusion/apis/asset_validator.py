from typing import List, cast

from starlette.datastructures import UploadFile

import facefusion.choices
from facefusion import ffmpeg
from facefusion.apis.asset_helper import detect_media_type_by_format
from facefusion.apis.media_validator import validate_media_resolution
from facefusion.filesystem import get_file_format
from facefusion.types import AudioFormat, ImageFormat, VideoFormat


def validate_subject(subject : str) -> bool:
	return subject in [ 'frame', 'face' ]


def validate_frame_index(frame_indexes : List[str]) -> bool:
	frame_min = 0
	frame_max = 101
	frame_total = len(frame_indexes)

	return frame_min < frame_total < frame_max


def validate_asset_type(upload_files : List[UploadFile]) -> bool:
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


def validate_asset_resolution(upload_files : List[UploadFile]) -> bool:
	for upload_file in upload_files:
		file_format = get_file_format(upload_file.filename)
		media_type = detect_media_type_by_format(file_format)

		if media_type in [ 'image', 'video' ]:
			media_buffer = upload_file.file.read()
			upload_file.file.seek(0)

			if not validate_media_resolution(media_buffer):
				return False

	return True
