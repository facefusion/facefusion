import subprocess
from pathlib import Path

import pytest

from facefusion import ffmpeg, ffprobe, process_manager, state_manager, vision
from facefusion.temp_helper import create_temp_directory, get_temp_file_path, resolve_temp_frame_paths


@pytest.mark.parametrize('encoder', [ 'libx264', 'libx265' ])
@pytest.mark.parametrize('strategy', [ 'memory', 'disk' ])
@pytest.mark.parametrize('sar, dar', [ ('4/3', '16:9'), ('1/1', '4:3') ])
def test_render_preserves_display_aspect(tmp_path : Path, encoder : str, strategy : str, sar : str, dar : str) -> None:
	target_path = str(tmp_path / 'input.mp4')
	output_path = str(tmp_path / 'output.mp4')
	subprocess.run([ 'ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=s=144x108:r=4:d=1', '-vf', 'setsar=' + sar, '-c:v', 'libx264', target_path ], check = True)
	state_manager.init()
	state_manager.init_item('temp_path', str(tmp_path))
	state_manager.init_item('target_path', target_path)
	state_manager.init_item('temp_frame_format', 'png')
	state_manager.init_item('temp_pixel_format', 'bgr24')
	state_manager.init_item('output_video_encoder', encoder)
	state_manager.init_item('output_video_preset', 'ultrafast')
	state_manager.init_item('output_video_quality', 80)
	process_manager.start()
	try:
		create_temp_directory(state_manager.get_temp_path(), output_path)
		if strategy == 'memory':
			raw_frames = subprocess.check_output([ 'ffmpeg', '-v', 'error', '-i', target_path, '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-' ])
			writer = ffmpeg.create_video_writer(output_path, 4, (144, 108), (144, 108), 4)
			writer.communicate(raw_frames)
			assert writer.returncode == 0
		else:
			assert ffmpeg.extract_frames(target_path, output_path, (144, 108), 4, 0, 4)
			for frame_path in resolve_temp_frame_paths(state_manager.get_temp_path(), output_path, 'png'):
				assert vision.write_image(frame_path, vision.read_image(frame_path))
			assert ffmpeg.merge_video(target_path, output_path, 4, 4, (144, 108), 0, 4)
		for video_path in [ target_path, get_temp_file_path(state_manager.get_temp_path(), output_path) ]:
			assert ffprobe.probe_video_entries(video_path, [ 'display_aspect_ratio', 'nb_frames' ]) == { 'display_aspect_ratio': dar, 'nb_frames': '4' }
	finally:
		process_manager.end()
