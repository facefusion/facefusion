import ctypes
from functools import partial
from unittest.mock import AsyncMock, MagicMock, patch

import cv2
import numpy
import pytest
from starlette.websockets import WebSocketState
from tests.assert_helper import get_test_example_file, get_test_examples_directory

from facefusion import rtc, rtc_store, state_manager
from facefusion.apis.stream_helper import cleanup_peer, decode_video_frame, drain_to_latest_frame, poll_for_buffer, poll_for_frame, process_image, process_video, receive_audio_frame, receive_video_buffer, receive_vision_frames, try_receive_frame
from facefusion.codecs import aom_decoder, aom_encoder, opus_decoder, opus_encoder, vpx_decoder, vpx_encoder
from facefusion.download import conditional_download
from facefusion.libraries import aom as aom_module, datachannel as datachannel_module, opus as opus_module, vpx as vpx_module
from facefusion.types import RtcPeer, VideoCodec
from facefusion.vision import read_video_frame


def rtc_receive_data(data : bytes, track : int, buffer : ctypes.Array[ctypes.c_char], size_byref : object) -> int:
	ctypes.memmove(buffer, data, len(data))
	ctypes.cast(size_byref, ctypes.POINTER(ctypes.c_int))[0] = len(data)
	return 0


def rtc_receive_once(data : bytes, state : list, track : int, buffer : ctypes.Array[ctypes.c_char], size_byref : object) -> int:
	if state[0]:
		return -1
	ctypes.memmove(buffer, data, len(data))
	ctypes.cast(size_byref, ctypes.POINTER(ctypes.c_int))[0] = len(data)
	state[0] = True
	return 0


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


@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8' ])
def test_cleanup_peer(video_codec : VideoCodec) -> None:
	session_id = 'test-cleanup-peer-' + video_codec
	peer_connection = rtc.create_peer_connection()
	rtc_peer : RtcPeer =\
	{
		'peer_connection': peer_connection,
		'video':
		{
			'sender_track': 0,
			'receiver_track': 0,
			'codec': video_codec
		}
	}

	rtc_store.init_peers(session_id)
	rtc_store.get_peers(session_id).append(rtc_peer)

	if video_codec == 'av1':
		cleanup_peer(session_id, rtc_peer, video_codec, aom_decoder.create(8), opus_decoder.create(48000, 2))
	if video_codec == 'vp8':
		cleanup_peer(session_id, rtc_peer, video_codec, vpx_decoder.create(8), opus_decoder.create(48000, 2))

	assert rtc_store.get_peers(session_id) is None
	assert datachannel_module.create_static_library().rtcDeletePeerConnection(peer_connection) == -1


@pytest.mark.parametrize('video_codec', [ 'av1', 'vp8' ])
def test_decode_video_frame(video_codec : VideoCodec) -> None:
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	video_resolution = (vision_frame.shape[1], vision_frame.shape[0])
	yuv_buffer = cv2.cvtColor(vision_frame, cv2.COLOR_BGR2YUV_I420).tobytes()

	if video_codec == 'av1':
		video_encoder = aom_encoder.create(video_resolution, 1000, 1, 0)
		encoded_buffer = aom_encoder.encode(video_encoder, yuv_buffer, video_resolution, 0)
		decoded_frame = decode_video_frame(video_codec, aom_decoder.create(8), encoded_buffer)

		assert decoded_frame is not None
		assert decoded_frame.shape[1] >= video_resolution[0]
		assert decoded_frame.shape[0] >= video_resolution[1]
		assert decoded_frame.ndim == 3

	if video_codec == 'vp8':
		video_encoder = vpx_encoder.create(video_resolution, 1000, 1, 0)
		encoded_buffer = vpx_encoder.encode(video_encoder, yuv_buffer, video_resolution, 0)
		decoded_frame = decode_video_frame(video_codec, vpx_decoder.create(8), encoded_buffer)

		assert decoded_frame is not None
		assert decoded_frame.shape[1] == video_resolution[0]
		assert decoded_frame.shape[0] == video_resolution[1]
		assert decoded_frame.ndim == 3


def test_decode_video_frame_empty_buffer() -> None:
	assert decode_video_frame('vp8', vpx_decoder.create(8), bytes()) is None
	assert decode_video_frame('av1', aom_decoder.create(8), bytes()) is None


def test_receive_video_buffer_failure() -> None:
	mock_lib = MagicMock()
	mock_lib.rtcReceiveMessage.return_value = -1
	receive_buffer = ctypes.create_string_buffer(512 * 1024)

	assert receive_video_buffer(mock_lib, 0, receive_buffer) is None


def test_receive_video_buffer_success() -> None:
	test_data = b'\x01\x02\x03\x04'
	mock_lib = MagicMock()
	mock_lib.rtcReceiveMessage.side_effect = partial(rtc_receive_data, test_data)

	assert receive_video_buffer(mock_lib, 0, ctypes.create_string_buffer(512 * 1024)) == test_data


def test_poll_for_buffer_timeout() -> None:
	mock_lib = MagicMock()
	mock_lib.rtcReceiveMessage.return_value = -1

	assert poll_for_buffer(mock_lib, 0, ctypes.create_string_buffer(512 * 1024), 0.01) is None


def test_poll_for_buffer_success() -> None:
	test_data = b'\x01\x02\x03\x04'
	mock_lib = MagicMock()
	mock_lib.rtcReceiveMessage.side_effect = partial(rtc_receive_data, test_data)

	assert poll_for_buffer(mock_lib, 0, ctypes.create_string_buffer(512 * 1024), 1.0) == test_data


def test_receive_audio_frame_failure() -> None:
	mock_lib = MagicMock()
	mock_lib.rtcReceiveMessage.return_value = -1
	result = receive_audio_frame(mock_lib, 0, opus_decoder.create(48000, 2), ctypes.create_string_buffer(8 * 1024))

	assert result.dtype == numpy.int16


def test_receive_audio_frame_success() -> None:
	audio_data = numpy.zeros(960 * 2, dtype = numpy.float32).tobytes()
	encoded_opus = opus_encoder.encode(opus_encoder.create(48000, 2), audio_data, 960)
	mock_lib = MagicMock()
	mock_lib.rtcReceiveMessage.side_effect = partial(rtc_receive_data, encoded_opus)
	result = receive_audio_frame(mock_lib, 0, opus_decoder.create(48000, 2), ctypes.create_string_buffer(8 * 1024))

	assert result.dtype == numpy.float32
	assert result.size == 960 * 2


def test_try_receive_frame_no_data() -> None:
	mock_lib = MagicMock()
	mock_lib.rtcReceiveMessage.return_value = -1

	assert try_receive_frame(mock_lib, 0, 'vp8', vpx_decoder.create(8), ctypes.create_string_buffer(512 * 1024)) is None


def test_try_receive_frame_valid_data() -> None:
	source_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	video_resolution = (source_frame.shape[1], source_frame.shape[0])
	yuv_buffer = cv2.cvtColor(source_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
	encoded_buffer = vpx_encoder.encode(vpx_encoder.create(video_resolution, 1000, 1, 0), yuv_buffer, video_resolution, 0)
	mock_lib = MagicMock()
	mock_lib.rtcReceiveMessage.side_effect = partial(rtc_receive_data, encoded_buffer)
	vision_frame = try_receive_frame(mock_lib, 0, 'vp8', vpx_decoder.create(8), ctypes.create_string_buffer(512 * 1024))

	assert vision_frame is not None
	assert vision_frame.shape[1] == video_resolution[0]
	assert vision_frame.shape[0] == video_resolution[1]


def test_drain_to_latest_frame_no_data() -> None:
	mock_lib = MagicMock()
	mock_lib.rtcReceiveMessage.return_value = -1

	assert drain_to_latest_frame(mock_lib, 0, 'vp8', vpx_decoder.create(8), ctypes.create_string_buffer(512 * 1024)) is None


def test_drain_to_latest_frame_returns_last_frame() -> None:
	source_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	video_resolution = (source_frame.shape[1], source_frame.shape[0])
	yuv_buffer = cv2.cvtColor(source_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
	encoded_buffer = vpx_encoder.encode(vpx_encoder.create(video_resolution, 1000, 1, 0), yuv_buffer, video_resolution, 0)
	mock_lib = MagicMock()
	mock_lib.rtcReceiveMessage.side_effect = partial(rtc_receive_once, encoded_buffer, [ False ])
	last_frame = drain_to_latest_frame(mock_lib, 0, 'vp8', vpx_decoder.create(8), ctypes.create_string_buffer(512 * 1024))

	assert last_frame is not None
	assert last_frame.shape[1] == video_resolution[0]
	assert last_frame.shape[0] == video_resolution[1]


def test_poll_for_frame_timeout() -> None:
	mock_lib = MagicMock()
	mock_lib.rtcReceiveMessage.return_value = -1

	assert poll_for_frame(mock_lib, 0, 'vp8', vpx_decoder.create(8), ctypes.create_string_buffer(512 * 1024), 0.01) is None


def test_poll_for_frame_success() -> None:
	source_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	video_resolution = (source_frame.shape[1], source_frame.shape[0])
	yuv_buffer = cv2.cvtColor(source_frame, cv2.COLOR_BGR2YUV_I420).tobytes()
	encoded_buffer = vpx_encoder.encode(vpx_encoder.create(video_resolution, 1000, 1, 0), yuv_buffer, video_resolution, 0)
	mock_lib = MagicMock()
	mock_lib.rtcReceiveMessage.side_effect = partial(rtc_receive_once, encoded_buffer, [ False ])
	last_frame = poll_for_frame(mock_lib, 0, 'vp8', vpx_decoder.create(8), ctypes.create_string_buffer(512 * 1024), 1.0)

	assert last_frame is not None
	assert last_frame.shape[1] == video_resolution[0]
	assert last_frame.shape[0] == video_resolution[1]


@pytest.fixture
def anyio_backend() -> str:
	return 'asyncio'


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


@pytest.mark.anyio
async def test_process_image_sends_processed_frame() -> None:
	vision_frame = read_video_frame(get_test_example_file('target-240p.mp4'))
	_, jpeg_buffer = cv2.imencode('.jpg', vision_frame)
	mock_ws = AsyncMock()
	mock_ws.scope = {'type': 'websocket', 'headers': []}
	mock_ws.client_state = WebSocketState.CONNECTED
	mock_ws.receive.side_effect = [{'type': 'websocket.receive', 'bytes': jpeg_buffer.tobytes()}]

	state_manager.init_item('source_paths', [get_test_example_file('source.jpg')])

	await process_image(mock_ws)

	mock_ws.accept.assert_called_once()
	mock_ws.send_bytes.assert_called_once()
	assert mock_ws.send_bytes.call_args[0][0][:3] == b'\xff\xd8\xff'


@pytest.mark.anyio
async def test_process_image_without_source_closes_cleanly() -> None:
	mock_ws = AsyncMock()
	mock_ws.scope = {'type': 'websocket', 'headers': []}
	mock_ws.client_state = WebSocketState.CONNECTED

	state_manager.init_item('source_paths', None)

	await process_image(mock_ws)

	mock_ws.accept.assert_called_once()
	mock_ws.send_bytes.assert_not_called()
	mock_ws.close.assert_called_once()


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
