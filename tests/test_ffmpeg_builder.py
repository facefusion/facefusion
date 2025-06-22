from shutil import which

from facefusion import ffmpeg_builder
from facefusion.ffmpeg_builder import chain, run, select_frame_range, set_audio_quality, set_audio_sample_size, set_stream_mode, set_video_quality


def test_run() -> None:
	assert run([]) == [ which('ffmpeg'), '-loglevel', 'error' ]


def test_chain() -> None:
	assert chain(ffmpeg_builder.set_progress()) == [ '-progress' ]


def test_set_stream_mode() -> None:
	assert set_stream_mode('udp') == [ '-f', 'mpegts' ]
	assert set_stream_mode('v4l2') == [ '-f', 'v4l2' ]


def test_select_frame_range() -> None:
	assert select_frame_range(0, None, 30) == [ '-vf', 'trim=start_frame=0,fps=30' ]
	assert select_frame_range(None, 100, 30) == [ '-vf', 'trim=end_frame=100,fps=30' ]
	assert select_frame_range(0, 100, 30) == [ '-vf', 'trim=start_frame=0:end_frame=100,fps=30' ]
	assert select_frame_range(None, None, 30) == [ '-vf', 'fps=30' ]


def test_set_audio_sample_size() -> None:
	assert set_audio_sample_size(16) == [ '-f', 's16le' ]
	assert set_audio_sample_size(32) == [ '-f', 's32le' ]


def test_set_audio_quality() -> None:
	assert set_audio_quality('aac', 0) == [ '-q:a', '0.1' ]
	assert set_audio_quality('aac', 50) == [ '-q:a', '1.0' ]
	assert set_audio_quality('aac', 100) == [ '-q:a', '2.0' ]
	assert set_audio_quality('libmp3lame', 0) == [ '-q:a', '9' ]
	assert set_audio_quality('libmp3lame', 50) == [ '-q:a', '4' ]
	assert set_audio_quality('libmp3lame', 100) == [ '-q:a', '0' ]
	assert set_audio_quality('libopus', 0) == [ '-b:a', '64k' ]
	assert set_audio_quality('libopus', 50) == [ '-b:a', '160k' ]
	assert set_audio_quality('libopus', 100) == [ '-b:a', '256k' ]
	assert set_audio_quality('libvorbis', 0) == [ '-q:a', '-1.0' ]
	assert set_audio_quality('libvorbis', 50) == [ '-q:a', '4.5' ]
	assert set_audio_quality('libvorbis', 100) == [ '-q:a', '10.0' ]
	assert set_audio_quality('flac', 0) == []
	assert set_audio_quality('flac', 50) == []
	assert set_audio_quality('flac', 100) == []


def test_set_video_quality() -> None:
	assert set_video_quality('libx264', 0) == [ '-crf', '51' ]
	assert set_video_quality('libx264', 50) == [ '-crf', '26' ]
	assert set_video_quality('libx264', 100) == [ '-crf', '0' ]
	assert set_video_quality('libx265', 0) == [ '-crf', '51' ]
	assert set_video_quality('libx265', 50) == [ '-crf', '26' ]
	assert set_video_quality('libx265', 100) == [ '-crf', '0' ]
	assert set_video_quality('libvpx-vp9', 0) == [ '-crf', '63' ]
	assert set_video_quality('libvpx-vp9', 50) == [ '-crf', '32' ]
	assert set_video_quality('libvpx-vp9', 100) == [ '-crf', '0' ]
	assert set_video_quality('h264_nvenc', 0) == [ '-cq' , '51' ]
	assert set_video_quality('h264_nvenc', 50) == [ '-cq' , '26' ]
	assert set_video_quality('h264_nvenc', 100) == [ '-cq' , '0' ]
	assert set_video_quality('hevc_nvenc', 0) == [ '-cq' , '51' ]
	assert set_video_quality('hevc_nvenc', 50) == [ '-cq' , '26' ]
	assert set_video_quality('hevc_nvenc', 100) == [ '-cq' , '0' ]
	assert set_video_quality('h264_amf', 0) == [ '-qp_i', '51', '-qp_p', '51', '-qp_b', '51' ]
	assert set_video_quality('h264_amf', 50) == [ '-qp_i', '26', '-qp_p', '26', '-qp_b', '26' ]
	assert set_video_quality('h264_amf', 100) == [ '-qp_i', '0', '-qp_p', '0', '-qp_b', '0' ]
	assert set_video_quality('hevc_amf', 0) == [ '-qp_i', '51', '-qp_p', '51', '-qp_b', '51' ]
	assert set_video_quality('hevc_amf', 50) == [ '-qp_i', '26', '-qp_p', '26', '-qp_b', '26' ]
	assert set_video_quality('hevc_amf', 100) == [ '-qp_i', '0', '-qp_p', '0', '-qp_b', '0' ]
	assert set_video_quality('h264_qsv', 0) == [ '-qp', '51' ]
	assert set_video_quality('h264_qsv', 50) == [ '-qp', '26' ]
	assert set_video_quality('h264_qsv', 100) == [ '-qp', '0' ]
	assert set_video_quality('hevc_qsv', 0) == [ '-qp', '51' ]
	assert set_video_quality('hevc_qsv', 50) == [ '-qp', '26' ]
	assert set_video_quality('hevc_qsv', 100) == [ '-qp', '0' ]
	assert set_video_quality('h264_videotoolbox', 0) == [ '-b:v', '1024k' ]
	assert set_video_quality('h264_videotoolbox', 50) == [ '-b:v', '25768k' ]
	assert set_video_quality('h264_videotoolbox', 100) == [ '-b:v', '50512k' ]
	assert set_video_quality('hevc_videotoolbox', 0) == [ '-b:v', '1024k' ]
	assert set_video_quality('hevc_videotoolbox', 50) == [ '-b:v', '25768k' ]
	assert set_video_quality('hevc_videotoolbox', 100) == [ '-b:v', '50512k' ]
