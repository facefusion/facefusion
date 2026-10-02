from shutil import which

from facefusion import ffmpeg_builder
from facefusion.ffmpeg_builder import capture_video, chain, concat, convert_color_space, deep_copy_audio, deep_copy_image, deep_copy_video, enforce_pixel_format, get_encoders, keep_video_alpha, map_amf_preset, map_nvenc_preset, map_qsv_preset, restrict_color_transfer, run, seek_to, select_frame_range, select_media_range, set_audio_quality, set_audio_sample_size, set_audio_volume, set_faststart, set_hardware_accelerator, set_image_quality, set_input_fps, set_loop, set_media_resolution, set_output_format, set_pixel_format, set_start_number, set_stream_mode, set_stream_quality, set_thread_count, set_video_duration, set_video_encoder, set_video_fps, set_video_preset, set_video_quality, set_video_tag, strip_metadata


def test_run() -> None:
	assert run([]) == [ which('ffmpeg'), '-loglevel', 'error' ]


def test_chain() -> None:
	assert chain(
		ffmpeg_builder.set_input('input.mp4'),
		ffmpeg_builder.set_output('output.mp4')
	) == [ '-i', 'input.mp4', 'output.mp4' ]
	assert chain(
		ffmpeg_builder.set_video_encoder('libx264'),
		ffmpeg_builder.set_video_fps(30),
		ffmpeg_builder.set_audio_encoder('aac')
	) == [ '-c:v', 'libx264', '-vf', 'fps=30', '-c:a', 'aac' ]


def test_concat() -> None:
	assert concat(
		set_video_encoder('libvpx-vp9'),
		set_video_fps(30)
	) == [ '-c:v', 'libvpx-vp9', '-vf', 'fps=30' ]
	assert concat(
		set_video_encoder('libvpx-vp9'),
		set_video_fps(30),
		keep_video_alpha('libvpx-vp9')
	) == [ '-c:v', 'libvpx-vp9', '-vf', 'fps=30,format=yuva420p' ]
	assert concat(
		select_frame_range(0, 100, 30),
		keep_video_alpha('libvpx-vp9')
	) == [ '-vf', 'trim=start_frame=0:end_frame=100,fps=30,format=yuva420p' ]
	assert concat(
		set_video_fps(25),
		convert_color_space('bt709')
	) == [ '-vf', 'fps=25,scale=out_color_matrix=bt709:out_range=tv,setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709' ]
	assert concat() == []


def test_get_encoders() -> None:
	assert get_encoders() == [ '-encoders' ]


def test_set_hardware_accelerator() -> None:
	assert set_hardware_accelerator('cuda') == [ '-hwaccel', 'cuda' ]


def test_seek_to() -> None:
	assert seek_to(0.0) == [ '-ss', '0.0' ]
	assert seek_to(1.5) == [ '-ss', '1.5' ]


def test_set_input_fps() -> None:
	assert set_input_fps(25.0) == [ '-r', '25.0' ]
	assert set_input_fps(29.97) == [ '-r', '29.97' ]


def test_set_start_number() -> None:
	assert set_start_number(0) == [ '-start_number', '0' ]
	assert set_start_number(124) == [ '-start_number', '124' ]


def test_set_output_format() -> None:
	assert set_output_format('rawvideo') == [ '-f', 'rawvideo' ]


def test_set_thread_count() -> None:
	assert set_thread_count(8) == [ '-threads', '8' ]
	assert set_thread_count(16) == [ '-threads', '16' ]


def test_set_loop() -> None:
	assert set_loop() == [ '-loop', '1' ]


def test_set_stream_mode() -> None:
	assert set_stream_mode('udp') == [ '-f', 'mpegts' ]
	assert set_stream_mode('v4l2') == [ '-f', 'v4l2' ]
	assert set_stream_mode('invalid') == []


def test_set_stream_quality() -> None:
	assert set_stream_quality(500) == [ '-b:v', '500k' ]
	assert set_stream_quality(2000) == [ '-b:v', '2000k' ]


def test_enforce_pixel_format() -> None:
	assert enforce_pixel_format('yuv420p') == [ '-pix_fmt', 'yuv420p' ]
	assert enforce_pixel_format('rgb24') == [ '-pix_fmt', 'rgb24' ]


def test_strip_metadata() -> None:
	assert strip_metadata() == [ '-map_metadata', '-1' ]


def test_set_pixel_format() -> None:
	assert set_pixel_format('rawvideo') == [ '-pix_fmt', 'rgb24' ]
	assert set_pixel_format('libvpx-vp9') == [ '-pix_fmt', 'yuva420p' ]
	assert set_pixel_format('libx264') == [ '-pix_fmt', 'yuv420p' ]
	assert set_pixel_format('h264_nvenc') == [ '-pix_fmt', 'yuv420p' ]


def test_restrict_color_transfer() -> None:
	assert restrict_color_transfer('smpte2084') == [ '-vf', 'scale=out_primaries=bt709:out_transfer=bt709:intent=perceptual' ]
	assert restrict_color_transfer('arib-std-b67') == [ '-vf', 'scale=out_primaries=bt709:out_transfer=bt709:intent=perceptual' ]
	assert restrict_color_transfer('invalid') == []


def test_convert_color_space() -> None:
	assert convert_color_space('bt601') == [ '-vf', 'scale=out_color_matrix=bt601:out_range=tv,setparams=colorspace=bt601:color_primaries=bt601:color_trc=bt601' ]
	assert convert_color_space('bt709') == [ '-vf', 'scale=out_color_matrix=bt709:out_range=tv,setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709' ]
	assert convert_color_space('bt2020') == [ '-vf', 'scale=out_color_matrix=bt2020:out_range=tv,setparams=colorspace=bt2020:color_primaries=bt2020:color_trc=bt2020' ]


def test_select_frame_range() -> None:
	assert select_frame_range(0, None, 30) == [ '-vf', 'trim=start_frame=0,fps=30' ]
	assert select_frame_range(None, 100, 30) == [ '-vf', 'trim=end_frame=100,fps=30' ]
	assert select_frame_range(0, 100, 30) == [ '-vf', 'trim=start_frame=0:end_frame=100,fps=30' ]
	assert select_frame_range(None, None, 30) == [ '-vf', 'fps=30' ]


def test_select_media_range() -> None:
	assert select_media_range(0, 270, 25) == [ '-ss', '0.0', '-to', '10.8' ]
	assert select_media_range(124, 224, 25) == [ '-ss', '4.96', '-to', '8.96' ]
	assert select_media_range(50, 150, 25.0) == [ '-ss', '2.0', '-to', '6.0' ]
	assert select_media_range(0, 100, 30) == [ '-ss', '0.0', '-to', '3.3333333333333335' ]
	assert select_media_range(30, 60, 29.97) == [ '-ss', '1.001001001001001', '-to', '2.002002002002002' ]
	assert select_media_range(124, None, 25) == [ '-ss', '4.96' ]
	assert select_media_range(None, 224, 25) == [ '-to', '8.96' ]
	assert select_media_range(None, None, 25) == []


def test_set_media_resolution() -> None:
	assert set_media_resolution('426x226') == [ '-s', '426x226' ]


def test_deep_copy_audio() -> None:
	assert deep_copy_audio() == [ '-q:a', '0' ]


def test_set_audio_sample_size() -> None:
	assert set_audio_sample_size(16) == [ '-f', 's16le' ]
	assert set_audio_sample_size(32) == [ '-f', 's32le' ]
	assert set_audio_sample_size(8) == []


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


def test_set_audio_volume() -> None:
	assert set_audio_volume(0) == [ '-filter:a', 'volume=0.0' ]
	assert set_audio_volume(75) == [ '-filter:a', 'volume=0.75' ]
	assert set_audio_volume(100) == [ '-filter:a', 'volume=1.0' ]
	assert set_audio_volume(200) == [ '-filter:a', 'volume=2.0' ]


def test_deep_copy_image() -> None:
	assert deep_copy_image() == [ '-q:v', '0' ]


def test_set_image_quality() -> None:
	assert set_image_quality('target.jpg', 0) == [ '-q:v', '31' ]
	assert set_image_quality('target.jpg', 50) == [ '-q:v', '16' ]
	assert set_image_quality('target.jpg', 80) == [ '-q:v', '6' ]
	assert set_image_quality('target.jpg', 100) == [ '-q:v', '0' ]
	assert set_image_quality('target.png', 100) == [ '-q:v', '0' ]
	assert set_image_quality('target.webp', 0) == [ '-q:v', '0' ]
	assert set_image_quality('target.webp', 80) == [ '-q:v', '80' ]
	assert set_image_quality('target.webp', 100) == [ '-q:v', '100' ]


def test_deep_copy_video() -> None:
	assert deep_copy_video() == [ '-q:v', '0' ]


def test_set_faststart() -> None:
	assert set_faststart('m4v') == [ '-movflags', '+faststart' ]
	assert set_faststart('mov') == [ '-movflags', '+faststart' ]
	assert set_faststart('mp4') == [ '-movflags', '+faststart' ]
	assert set_faststart('mkv') == []
	assert set_faststart('webm') == []


def test_set_video_tag() -> None:
	assert set_video_tag('libx265', 'm4v') == [ '-tag:v', 'hvc1' ]
	assert set_video_tag('hevc_nvenc', 'mov') == [ '-tag:v', 'hvc1' ]
	assert set_video_tag('hevc_videotoolbox', 'mp4') == [ '-tag:v', 'hvc1' ]
	assert set_video_tag('libx265', 'mkv') == []
	assert set_video_tag('libx265', 'webm') == []
	assert set_video_tag('libx264', 'mp4') == []
	assert set_video_tag('h264_nvenc', 'mp4') == []


def test_set_video_quality() -> None:
	assert set_video_quality('libx264', 0) == [ '-crf', '51' ]
	assert set_video_quality('libx264', 50) == [ '-crf', '26' ]
	assert set_video_quality('libx264', 100) == [ '-crf', '0' ]
	assert set_video_quality('libx264rgb', 0) == [ '-crf', '51' ]
	assert set_video_quality('libx264rgb', 50) == [ '-crf', '26' ]
	assert set_video_quality('libx264rgb', 100) == [ '-crf', '0' ]
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
	assert set_video_quality('rawvideo', 100) == []


def test_set_video_preset() -> None:
	assert set_video_preset('libx264', 'ultrafast') == [ '-preset', 'ultrafast' ]
	assert set_video_preset('libx264rgb', 'medium') == [ '-preset', 'medium' ]
	assert set_video_preset('libx265', 'veryslow') == [ '-preset', 'veryslow' ]
	assert set_video_preset('h264_nvenc', 'ultrafast') == [ '-preset', 'fast' ]
	assert set_video_preset('hevc_nvenc', 'veryslow') == [ '-preset', 'slow' ]
	assert set_video_preset('h264_amf', 'ultrafast') == [ '-quality', 'speed' ]
	assert set_video_preset('hevc_amf', 'veryslow') == [ '-quality', 'quality' ]
	assert set_video_preset('h264_qsv', 'ultrafast') == [ '-preset', 'veryfast' ]
	assert set_video_preset('hevc_qsv', 'slower') == [ '-preset', 'slower' ]
	assert set_video_preset('libvpx-vp9', 'ultrafast') == []
	assert set_video_preset('rawvideo', 'medium') == []


def test_set_video_fps() -> None:
	assert set_video_fps(25) == [ '-vf', 'fps=25' ]
	assert set_video_fps(29.97) == [ '-vf', 'fps=29.97' ]


def test_set_video_duration() -> None:
	assert set_video_duration(1.0) == [ '-t', '1.0' ]
	assert set_video_duration(10.8) == [ '-t', '10.8' ]


def test_keep_video_alpha() -> None:
	assert keep_video_alpha('libvpx-vp9') == [ '-vf', 'format=yuva420p' ]
	assert keep_video_alpha('libx264') == []


def test_capture_video() -> None:
	assert capture_video() == [ '-f', 'rawvideo', '-pix_fmt', 'rgb24' ]


def test_map_nvenc_preset() -> None:
	assert map_nvenc_preset('ultrafast') == 'fast'
	assert map_nvenc_preset('superfast') == 'fast'
	assert map_nvenc_preset('veryfast') == 'fast'
	assert map_nvenc_preset('faster') == 'fast'
	assert map_nvenc_preset('fast') == 'fast'
	assert map_nvenc_preset('medium') == 'medium'
	assert map_nvenc_preset('slow') == 'slow'
	assert map_nvenc_preset('slower') == 'slow'
	assert map_nvenc_preset('veryslow') == 'slow'
	assert map_nvenc_preset('invalid') is None


def test_map_amf_preset() -> None:
	assert map_amf_preset('ultrafast') == 'speed'
	assert map_amf_preset('superfast') == 'speed'
	assert map_amf_preset('veryfast') == 'speed'
	assert map_amf_preset('faster') == 'balanced'
	assert map_amf_preset('fast') == 'balanced'
	assert map_amf_preset('medium') == 'balanced'
	assert map_amf_preset('slow') == 'quality'
	assert map_amf_preset('slower') == 'quality'
	assert map_amf_preset('veryslow') == 'quality'
	assert map_amf_preset('invalid') is None


def test_map_qsv_preset() -> None:
	assert map_qsv_preset('ultrafast') == 'veryfast'
	assert map_qsv_preset('superfast') == 'veryfast'
	assert map_qsv_preset('veryfast') == 'veryfast'
	assert map_qsv_preset('faster') == 'faster'
	assert map_qsv_preset('fast') == 'fast'
	assert map_qsv_preset('medium') == 'medium'
	assert map_qsv_preset('slow') == 'slow'
	assert map_qsv_preset('slower') == 'slower'
	assert map_qsv_preset('veryslow') == 'veryslow'
	assert map_qsv_preset('invalid') is None
