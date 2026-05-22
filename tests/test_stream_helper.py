import queue
import threading
from unittest.mock import AsyncMock, MagicMock, patch

import cv2
import numpy
import pytest
from starlette.websockets import WebSocketState
from tests.assert_helper import get_test_example_file, get_test_examples_directory

from facefusion import rtc, rtc_store, state_manager
from facefusion.apis.endpoints.stream import websocket_stream
from facefusion.apis.stream_helper import decode_video_frame, process_image, process_video, receive_audio_frames, receive_video_frames, receive_vision_frames, run_peer_loop
from facefusion.codecs import aom_decoder, aom_encoder, vpx_decoder, vpx_encoder
from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.download import conditional_download
from facefusion.hash_helper import create_hash
from facefusion.libraries import aom as aom_module, datachannel as datachannel_module, opus as opus_module, vpx as vpx_module
from facefusion.types import AudioFrame, RtcPeer, VideoCodec, VisionFrame
from facefusion.vision import read_video_frame


@pytest.fixture(scope = 'module', autouse = True)
def before_all() -> None:
	state_manager.init_item('download_providers', [ 'github', 'huggingface' ])
	state_manager.init_item('processors', [])

	conditional_download(get_test_examples_directory(),
	[
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/target-240p.mp4',
		'https://github.com/facefusion/facefusion-assets/releases/download/examples-3.0.0/source.jpg'
	])

	aom_module.pre_check()
	vpx_module.pre_check()
	opus_module.pre_check()
	datachannel_module.pre_check()


@pytest.fixture(scope = 'function', autouse = True)
def before_each() -> None:
	rtc_store.clear()


# TODO: refine test
@pytest.mark.parametrize('video_codec', ['av1', 'vp8'])
def test_decode_video_frame(video_codec: VideoCodec) -> None:
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	video_resolution = (vision_frame.shape[1], vision_frame.shape[0])
	frame_buffer = cv2.cvtColor(vision_frame, cv2.COLOR_BGR2YUV_I420).tobytes()

	if video_codec == 'av1':
		encode_frame_buffer = aom_encoder.encode(aom_encoder.create(video_resolution, 1000, 1, 0), frame_buffer,
												 video_resolution, 0)
		decode_frame_buffer = decode_video_frame(video_codec, aom_decoder.create(8), encode_frame_buffer).tobytes()

		if is_linux() or is_windows():
			assert create_hash(decode_frame_buffer) == '299b6ad6'

		if is_macos():
			assert create_hash(decode_frame_buffer) == '9f463b13'

		assert decode_video_frame('av1', aom_decoder.create(8), bytes()) is None

	if video_codec == 'vp8':
		encode_frame_buffer = vpx_encoder.encode(vpx_encoder.create(video_resolution, 1000, 1, 0), frame_buffer,
												 video_resolution, 0)
		decode_frame_buffer = decode_video_frame(video_codec, vpx_decoder.create(8), encode_frame_buffer).tobytes()

		if is_linux() or is_windows():
			assert create_hash(decode_frame_buffer) == '99ef2c25'

		if is_macos():
			assert create_hash(decode_frame_buffer) == 'ff3ecb43'

		assert decode_video_frame('vp8', vpx_decoder.create(8), bytes()) is None


# TODO: refine test
def test_receive_video_frames() -> None:
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	datachannel_library_mock = MagicMock()
	datachannel_library_mock.rtcReceiveMessage.side_effect = [ 0, -1 ]
	video_queue : queue.Queue[VisionFrame] = queue.Queue(maxsize = 1)

	with patch('facefusion.apis.stream_helper.datachannel_module.create_static_library', return_value = datachannel_library_mock), \
		patch('facefusion.apis.stream_helper.decode_video_frame', return_value = vision_frame):
		receiver_thread = threading.Thread(target = receive_video_frames, args = (0, 'vp8', video_queue), daemon = True)
		receiver_thread.start()
		receiver_thread.join(timeout = 2.0)

	assert create_hash(video_queue.get_nowait().tobytes()) == 'a17439db'


# TODO: refine test
def test_receive_audio_frames() -> None:
	audio_frame = numpy.zeros(960 * 2, dtype = numpy.float32)
	datachannel_library_mock = MagicMock()
	datachannel_library_mock.rtcReceiveMessage.side_effect = [ 0, -1 ]
	audio_queue : queue.Queue[AudioFrame] = queue.Queue(maxsize = 4)

	with patch('facefusion.apis.stream_helper.datachannel_module.create_static_library', return_value = datachannel_library_mock), \
		patch('facefusion.apis.stream_helper.opus_decoder.decode', return_value = audio_frame.tobytes()):
		receiver_thread = threading.Thread(target = receive_audio_frames, args = (0, audio_queue), daemon = True)
		receiver_thread.start()
		audio_frame = audio_queue.get(timeout = 2.0)
		receiver_thread.join(timeout = 1.0)

	assert audio_frame.dtype == numpy.float32
	assert audio_frame.size == 960 * 2
	assert audio_queue.empty()


# TODO: refine test
def test_run_peer_loop() -> None:
	source_frame = read_video_frame(get_test_example_file('target-240p.mp4'))

	peer_connection = rtc.create_peer_connection()
	video_sender_track = rtc.add_video_track(peer_connection, 'sendonly', 'vp8', 96)
	video_receiver_track = rtc.add_video_track(peer_connection, 'recvonly', 'vp8', 96)
	rtc_peer : RtcPeer =\
	{
		'peer_connection': peer_connection,
		'video':
		{
			'sender_track': video_sender_track,
			'receiver_track': video_receiver_track,
			'codec': 'vp8'
		}
	}

	session_id = 'test-run-peer-loop'
	rtc_store.init_peers(session_id)
	rtc_store.get_peers(session_id).append(rtc_peer)

	datachannel_library_mock = MagicMock()
	datachannel_library_mock.rtcReceiveMessage.side_effect = [ 0, -1 ]

	with patch('facefusion.apis.stream_helper.datachannel_module.create_static_library', return_value = datachannel_library_mock), \
		patch('facefusion.apis.stream_helper.decode_video_frame', return_value = source_frame), \
		patch('facefusion.apis.stream_helper.rtc.send_video') as mock_send_video:
		thread = threading.Thread(target = run_peer_loop, args = (session_id, rtc_peer), daemon = True)
		thread.start()
		thread.join(timeout = 5.0)

	assert mock_send_video.called
	assert len(mock_send_video.call_args[0][1]) > 0


# TODO: refine test
@pytest.mark.anyio
async def test_receive_vision_frames() -> None:
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	frame_buffer = cv2.imencode('.jpg', vision_frame)[1].tobytes()
	websocket_mock = AsyncMock()
	websocket_mock.receive.side_effect =\
	[
		{
			'type': 'websocket.receive',
			'bytes': frame_buffer
		},
		{
			'type': 'websocket.receive',
			'bytes': b'invalid'
		},
		{
			'type': 'websocket.receive',
			'bytes': frame_buffer
		},
		{
			'type': 'websocket.disconnect'
		}
	]

	frames = []

	async for frame in receive_vision_frames(websocket_mock):
		frames.append(frame)

	assert len(frames) == 2
	assert frames[0].shape == vision_frame.shape


# TODO: refine test
@pytest.mark.anyio
async def test_process_image() -> None:
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	frame_buffer = cv2.imencode('.jpg', vision_frame)[1].tobytes()
	websocket_mock = AsyncMock()
	websocket_mock.receive.side_effect = [{'type': 'websocket.receive', 'bytes': frame_buffer}]

	state_manager.init_item('source_paths', [get_test_example_file('source.jpg')])
	await process_image(websocket_mock)

	websocket_mock.send_bytes.assert_called_once()
	assert websocket_mock.send_bytes.call_args[0][0][:3] == b'\xff\xd8\xff'

	state_manager.init_item('source_paths', None)
	await process_image(websocket_mock)

	websocket_mock.send_bytes.assert_called_once()


# TODO: refine test
@pytest.mark.anyio
async def test_websocket_stream() -> None:
	websocket_mock = AsyncMock()
	websocket_mock.scope =\
	{
		'type': 'websocket',
		'headers': []
	}
	websocket_mock.client_state = WebSocketState.CONNECTED

	state_manager.init_item('source_paths', None)

	with patch('facefusion.apis.endpoints.stream.get_sec_websocket_protocol', return_value = None), \
		patch('facefusion.apis.endpoints.stream.extract_access_token', return_value = None), \
		patch('facefusion.apis.endpoints.stream.session_manager.find_session_id', return_value = None), \
		patch('facefusion.apis.endpoints.stream.session_context.set_session_id'):
		await websocket_stream(websocket_mock)

	websocket_mock.accept.assert_called_once()
	websocket_mock.close.assert_called_once()


# TODO: refine test
@pytest.mark.anyio
@pytest.mark.parametrize('video_codec, session_id', [ ('av1', 'test-process-video-av1'), ('vp8', 'test-process-video-vp8') ])
async def test_process_video(video_codec : VideoCodec, session_id : str) -> None:
	sender_connection = rtc.create_peer_connection()

	if video_codec == 'av1':
		rtc.add_video_track(sender_connection, 'sendrecv', video_codec, 35)
	if video_codec == 'vp8':
		rtc.add_video_track(sender_connection, 'sendrecv', video_codec, 96)

	rtc.add_audio_track(sender_connection, 'sendrecv', 'opus', 111)
	sdp_offer = rtc.create_sdp_offer(sender_connection)
	datachannel_module.create_static_library().rtcDeletePeerConnection(sender_connection)

	with patch('facefusion.apis.stream_helper.threading.Thread'):
		sdp_answer = process_video(session_id, sdp_offer)

	assert sdp_answer
	assert 'm=video' in sdp_answer
	assert 'a=recvonly' in sdp_answer
	assert 'a=sendonly' in sdp_answer
