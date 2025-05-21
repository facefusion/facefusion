from facefusion import ffmpeg_builder
from facefusion.ffmpeg import run_ffmpeg
from facefusion.filesystem import get_file_size
from facefusion.temp_helper import create_temp_directory, get_temp_file_path


def convert_video_to_playable_mp4(video_path : str) -> str:
	video_file_size = get_file_size(video_path)
	max_file_size = 512 * 1024 * 1024

	create_temp_directory(video_path)
	temp_video_path = get_temp_file_path(video_path)
	commands = ffmpeg_builder.set_input(video_path)

	if video_file_size > max_file_size:
		commands.extend(ffmpeg_builder.set_video_duration(10))

	commands.extend(ffmpeg_builder.force_output(temp_video_path))

	process = run_ffmpeg(commands)
	process.communicate()

	if process.returncode == 0:
		return temp_video_path

	return video_path


def check_allowed(path : str, check_in_upload_folder : bool) -> None:
	return None
