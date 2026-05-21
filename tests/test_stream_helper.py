import ctypes
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
from facefusion.codecs import aom_decoder, aom_encoder, opus_encoder, vpx_decoder, vpx_encoder
from facefusion.download import conditional_download
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
@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8' ])
def test_decode_video_frame(video_codec : VideoCodec) -> None:
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	video_resolution = (vision_frame.shape[1], vision_frame.shape[0])
	yuv_buffer = cv2.cvtColor(vision_frame, cv2.COLOR_BGR2YUV_I420).tobytes()

	if video_codec == 'av1':
		encoded_buffer = aom_encoder.encode(aom_encoder.create(video_resolution, 1000, 1, 0), yuv_buffer, video_resolution, 0)
		decoded_frame = decode_video_frame(video_codec, aom_decoder.create(8), encoded_buffer)

		assert decoded_frame is not None
		assert decoded_frame.shape[1] >= video_resolution[0]
		assert decoded_frame.shape[0] >= video_resolution[1]
		assert decoded_frame.ndim == 3

	if video_codec == 'vp8':
		encoded_buffer = vpx_encoder.encode(vpx_encoder.create(video_resolution, 1000, 1, 0), yuv_buffer, video_resolution, 0)
		decoded_frame = decode_video_frame(video_codec, vpx_decoder.create(8), encoded_buffer)

		assert decoded_frame is not None
		assert decoded_frame.shape[1] == video_resolution[0]
		assert decoded_frame.shape[0] == video_resolution[1]
		assert decoded_frame.ndim == 3


# TODO: refine test
def test_decode_video_frame_empty_buffer() -> None:
	assert decode_video_frame('vp8', vpx_decoder.create(8), bytes()) is None
	assert decode_video_frame('av1', aom_decoder.create(8), bytes()) is None


# TODO: refine test
def test_receive_video_frames_keeps_latest_when_full() -> None:
	source_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	video_resolution = (source_frame.shape[1], source_frame.shape[0])
	yuv_buffer = cv2.cvtColor(source_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
	encoded_buffer = vpx_encoder.encode(vpx_encoder.create(video_resolution, 1000, 1, 0), yuv_buffer, video_resolution, 0)
	mock_lib = MagicMock()
	state : list[int] = [ 0 ]

	def receive_two(track : int, buffer : ctypes.Array[ctypes.c_char], size_byref : ctypes.c_void_p) -> int:
		if state[0] < 2:
			ctypes.memmove(buffer, encoded_buffer, len(encoded_buffer))
			ctypes.cast(size_byref, ctypes.POINTER(ctypes.c_int))[0] = len(encoded_buffer)
			state[0] += 1
			return 0
		return -1

	mock_lib.rtcReceiveMessage.side_effect = receive_two
	video_queue : queue.Queue[VisionFrame] = queue.Queue(maxsize = 1)

	with patch('facefusion.apis.stream_helper.datachannel_module.create_static_library', return_value = mock_lib):
		receiver = threading.Thread(target = receive_video_frames, args = (0, 'vp8', video_queue), daemon = True)
		receiver.start()
		receiver.join(timeout = 2.0)

	assert video_queue.qsize() == 1
	assert video_queue.get_nowait().shape[1] == video_resolution[0]


# TODO: refine test
def test_receive_audio_frames_delivers_decoded_frame() -> None:
	audio_data = numpy.zeros(960 * 2, dtype = numpy.float32).tobytes()
	encoded_opus = opus_encoder.encode(opus_encoder.create(48000, 2), audio_data, 960)
	mock_lib = MagicMock()
	state : list[bool] = [ False ]

	def receive_once(track : int, buffer : ctypes.Array[ctypes.c_char], size_byref : ctypes.c_void_p) -> int:
		if state[0]:
			return -1
		ctypes.memmove(buffer, encoded_opus, len(encoded_opus))
		ctypes.cast(size_byref, ctypes.POINTER(ctypes.c_int))[0] = len(encoded_opus)
		state[0] = True
		return 0

	mock_lib.rtcReceiveMessage.side_effect = receive_once
	audio_queue : queue.Queue[AudioFrame] = queue.Queue(maxsize = 4)

	with patch('facefusion.apis.stream_helper.datachannel_module.create_static_library', return_value = mock_lib):
		receiver = threading.Thread(target = receive_audio_frames, args = (0, audio_queue), daemon = True)
		receiver.start()
		audio_frame = audio_queue.get(timeout = 2.0)
		receiver.join(timeout = 1.0)

	assert audio_frame.dtype == numpy.float32
	assert audio_frame.size == 960 * 2


# TODO: refine test
def test_receive_audio_frames_skips_empty_frames() -> None:
	mock_lib = MagicMock()
	mock_lib.rtcReceiveMessage.return_value = -1
	audio_queue : queue.Queue[AudioFrame] = queue.Queue(maxsize = 4)

	with patch('facefusion.apis.stream_helper.datachannel_module.create_static_library', return_value = mock_lib):
		receiver = threading.Thread(target = receive_audio_frames, args = (0, audio_queue), daemon = True)
		receiver.start()
		receiver.join(timeout = 0.1)

	assert audio_queue.empty()


# TODO: refine test
def test_run_peer_loop_processes_and_sends_frame() -> None:
	source_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	video_resolution = (source_frame.shape[1], source_frame.shape[0])
	yuv_buffer = cv2.cvtColor(source_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
	encoded_buffer = vpx_encoder.encode(vpx_encoder.create(video_resolution, 1000, 1, 0), yuv_buffer, video_resolution, 0)

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

	mock_lib = MagicMock()
	state : list[bool] = [ False ]

	def receive_once(track : int, buffer : ctypes.Array[ctypes.c_char], size_byref : ctypes.c_void_p) -> int:
		if state[0]:
			return -1
		ctypes.memmove(buffer, encoded_buffer, len(encoded_buffer))
		ctypes.cast(size_byref, ctypes.POINTER(ctypes.c_int))[0] = len(encoded_buffer)
		state[0] = True
		return 0

	mock_lib.rtcReceiveMessage.side_effect = receive_once

	with patch('facefusion.apis.stream_helper.datachannel_module.create_static_library', return_value = mock_lib), \
		patch('facefusion.apis.stream_helper.rtc.send_video') as mock_send_video:
		thread = threading.Thread(target = run_peer_loop, args = (session_id, rtc_peer), daemon = True)
		thread.start()
		thread.join(timeout = 5.0)

	assert mock_send_video.called
	assert len(mock_send_video.call_args[0][1]) > 0


# TODO: refine test
@pytest.mark.anyio
async def test_receive_vision_frames_yields_decoded_frames() -> None:
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	_, jpeg_buffer = cv2.imencode('.jpg', vision_frame)
	jpeg_bytes = jpeg_buffer.tobytes()
	mock_ws = AsyncMock()
	mock_ws.receive.side_effect =\
	[
		{'type': 'websocket.receive', 'bytes': jpeg_bytes},
		{'type': 'websocket.receive', 'bytes': jpeg_bytes},
		{'type': 'websocket.disconnect'}
	]

	frames = []

	async for frame in receive_vision_frames(mock_ws):
		frames.append(frame)

	assert len(frames) == 2
	assert frames[0].shape == vision_frame.shape


# TODO: refine test
@pytest.mark.anyio
async def test_receive_vision_frames_skips_invalid_bytes() -> None:
	mock_ws = AsyncMock()
	mock_ws.receive.side_effect =\
	[
		{'type': 'websocket.receive', 'bytes': b'not_a_jpeg'},
		{'type': 'websocket.disconnect'}
	]

	frames = []

	async for frame in receive_vision_frames(mock_ws):
		frames.append(frame)

	assert len(frames) == 0


# TODO: refine test
@pytest.mark.anyio
async def test_process_image_sends_processed_frame() -> None:
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	_, jpeg_buffer = cv2.imencode('.jpg', vision_frame)
	mock_ws = AsyncMock()
	mock_ws.receive.side_effect = [{'type': 'websocket.receive', 'bytes': jpeg_buffer.tobytes()}]

	state_manager.init_item('source_paths', [get_test_example_file('source.jpg')])

	await process_image(mock_ws)

	mock_ws.send_bytes.assert_called_once()
	assert mock_ws.send_bytes.call_args[0][0][:3] == b'\xff\xd8\xff'


# TODO: refine test
@pytest.mark.anyio
async def test_process_image_without_source_skips_send() -> None:
	mock_ws = AsyncMock()

	state_manager.init_item('source_paths', None)

	await process_image(mock_ws)

	mock_ws.send_bytes.assert_not_called()


# TODO: refine test
@pytest.mark.anyio
async def test_websocket_stream_accepts_and_closes() -> None:
	mock_ws = AsyncMock()
	mock_ws.scope = {'type': 'websocket', 'headers': []}
	mock_ws.client_state = WebSocketState.CONNECTED

	state_manager.init_item('source_paths', None)

	with patch('facefusion.apis.endpoints.stream.get_sec_websocket_protocol', return_value = None), \
		patch('facefusion.apis.endpoints.stream.extract_access_token', return_value = None), \
		patch('facefusion.apis.endpoints.stream.session_manager.find_session_id', return_value = None), \
		patch('facefusion.apis.endpoints.stream.session_context.set_session_id'):
		await websocket_stream(mock_ws)

	mock_ws.accept.assert_called_once()
	mock_ws.close.assert_called_once()


# TODO: refine test
@pytest.mark.anyio
@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8' ])
async def test_process_video_returns_sdp_answer(video_codec : VideoCodec) -> None:
	sender_connection = rtc.create_peer_connection()

	if video_codec == 'av1':
		rtc.add_video_track(sender_connection, 'sendrecv', video_codec, 35)
	if video_codec == 'vp8':
		rtc.add_video_track(sender_connection, 'sendrecv', video_codec, 96)

	rtc.add_audio_track(sender_connection, 'sendrecv', 'opus', 111)
	sdp_offer = rtc.create_sdp_offer(sender_connection)
	datachannel_module.create_static_library().rtcDeletePeerConnection(sender_connection)

	with patch('facefusion.apis.stream_helper.run_peer_loop'):
		sdp_answer = process_video('test-process-video-' + video_codec, sdp_offer)

	assert sdp_answer is not None
	assert 'm=video' in sdp_answer
	assert 'a=recvonly' in sdp_answer
	assert 'a=sendonly' in sdp_answer
