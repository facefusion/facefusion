import asyncio
import queue
from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import cv2
import numpy
import pytest
from numpy.typing import NDArray
from starlette.websockets import WebSocketState

from facefusion.apis.stream_helper import handle_video_stream, receive_stream_frames, receive_vision_frames, run_aom_encode_loop, run_opus_encode_loop, run_vp8_encode_loop
from facefusion.common_helper import is_linux, is_macos, is_windows
from facefusion.hash_helper import create_hash
from facefusion.types import VisionFrame


# TODO: inline or move to helper
async def _collect_stream_frames(events : list[Any]) -> list[tuple[int, bytes]]:
	return [ item async for item in receive_stream_frames(_make_websocket(events)) ]


# TODO: inline or move to helper
async def _collect_vision_frames(events : list[Any]) -> list[NDArray[Any]]:
	return [ item async for item in receive_vision_frames(_make_websocket(events)) ]


# TODO: inline or move to helper
def _make_websocket(events : list[Any]) -> MagicMock:
	mock = MagicMock()
	mock.receive = AsyncMock(side_effect = events)
	return mock


# TODO: inline or move to helper
def _make_handler_websocket(events : list[Any]) -> MagicMock:
	mock = MagicMock()
	mock.scope = {}
	mock.client_state = WebSocketState.CONNECTED
	mock.accept = AsyncMock()
	mock.send_text = AsyncMock()
	mock.close = AsyncMock()
	mock.receive = AsyncMock(side_effect = events)
	return mock


# TODO: inline or move to helper
def _make_video_packet(frame : NDArray[Any]) -> bytes:
	_, encoded = cv2.imencode('.jpg', frame)
	return b'\x01' + encoded.tobytes()

# TODO: inline or move to helper
def _make_audio_packet(samples : NDArray[Any]) -> bytes:
	return b'\x02' + samples.tobytes()


# TODO: refine test
def test_receive_stream_frames() -> None:
	frame = numpy.full((64, 64, 3), 128, dtype = numpy.uint8)
	video_packet = _make_video_packet(frame)
	audio_packet = _make_audio_packet(numpy.zeros(1920, dtype = numpy.float32))

	result = asyncio.run(_collect_stream_frames([ {'type': 'websocket.receive', 'bytes': video_packet}, {'type': 'websocket.disconnect'} ]))
	assert len(result) == 1
	assert result[0][0] == 1

	if is_linux() or is_windows():
		assert create_hash(result[0][1]) == '8ba34289'

	if is_macos():
		pytest.skip()

	result = asyncio.run(_collect_stream_frames([ {'type': 'websocket.receive', 'bytes': audio_packet}, {'type': 'websocket.disconnect'} ]))
	assert len(result) == 1
	assert result[0][0] == 2

	assert asyncio.run(_collect_stream_frames([ {'type': 'websocket.receive', 'bytes': b'\x01'}, {'type': 'websocket.receive', 'bytes': b''}, {'type': 'websocket.receive', 'bytes': None}, {'type': 'websocket.disconnect'} ])) == []

	assert len(asyncio.run(_collect_stream_frames([ {'type': 'websocket.receive', 'bytes': video_packet}, {'type': 'websocket.disconnect'}, {'type': 'websocket.receive', 'bytes': video_packet} ]))) == 1


# TODO: refine test
def test_receive_vision_frames() -> None:
	frame = numpy.full((64, 64, 3), 128, dtype = numpy.uint8)
	_, encoded = cv2.imencode('.jpg', frame)

	result = asyncio.run(_collect_vision_frames([ {'type': 'websocket.receive', 'bytes': encoded.tobytes()}, {'type': 'websocket.disconnect'} ]))
	assert len(result) == 1

	if is_linux() or is_windows():
		assert create_hash(result[0].tobytes()) == 'df269b74'

	if is_macos():
		assert create_hash(result[0].tobytes()) == 'df269b74'

	assert asyncio.run(_collect_vision_frames([ {'type': 'websocket.receive', 'bytes': b'not_an_image'}, {'type': 'websocket.disconnect'} ])) == []


# TODO: refine test
def test_run_vp8_encode_loop() -> None:
	frame = numpy.full((64, 64, 3), 128, dtype = numpy.uint8)
	small_frame = numpy.full((64, 64, 3), 128, dtype = numpy.uint8)
	large_frame = numpy.full((128, 128, 3), 128, dtype = numpy.uint8)
	black_frame = numpy.zeros((64, 64, 3), dtype = numpy.uint8)

	vision_frame_queue : queue.Queue[Optional[VisionFrame]] = queue.Queue()
	vision_frame_queue.put(frame)
	vision_frame_queue.put(None)
	with patch('facefusion.apis.stream_helper.process_vision_frame', return_value = frame), \
		patch('facefusion.apis.stream_helper.create_vpx_encoder', return_value = MagicMock()), \
		patch('facefusion.apis.stream_helper.encode_vpx_buffer', return_value = b'encoded'), \
		patch('facefusion.apis.stream_helper.destroy_vpx_encoder'), \
		patch('facefusion.apis.stream_helper.rtc_store') as mock_rtc_store, \
		patch('facefusion.apis.stream_helper.rtc') as mock_rtc:
		mock_rtc_store.get_rtc_peers.return_value = [ MagicMock() ]
		run_vp8_encode_loop(vision_frame_queue, 'session-1', (64, 64))
		mock_rtc.send_video_to_peers.assert_called_once()

	vision_frame_queue = queue.Queue()
	vision_frame_queue.put(small_frame)
	vision_frame_queue.put(small_frame)
	vision_frame_queue.put(None)
	with patch('facefusion.apis.stream_helper.process_vision_frame', return_value = large_frame), \
		patch('facefusion.apis.stream_helper.create_vpx_encoder', return_value = MagicMock()) as mock_create, \
		patch('facefusion.apis.stream_helper.encode_vpx_buffer', return_value = None), \
		patch('facefusion.apis.stream_helper.destroy_vpx_encoder') as mock_destroy, \
		patch('facefusion.apis.stream_helper.rtc_store'), \
		patch('facefusion.apis.stream_helper.rtc'):
		run_vp8_encode_loop(vision_frame_queue, 'session-1', (64, 64))
		assert mock_create.call_count == 2
		assert mock_destroy.call_count == 2

	vision_frame_queue = queue.Queue()
	vision_frame_queue.put(frame)
	vision_frame_queue.put(None)
	with patch('facefusion.apis.stream_helper.process_vision_frame', return_value = frame), \
		patch('facefusion.apis.stream_helper.create_vpx_encoder', return_value = MagicMock()), \
		patch('facefusion.apis.stream_helper.encode_vpx_buffer', return_value = b''), \
		patch('facefusion.apis.stream_helper.destroy_vpx_encoder'), \
		patch('facefusion.apis.stream_helper.rtc_store'), \
		patch('facefusion.apis.stream_helper.rtc') as mock_rtc:
		run_vp8_encode_loop(vision_frame_queue, 'session-1', (64, 64))
		mock_rtc.send_video_to_peers.assert_not_called()

	vision_frame_queue = queue.Queue()
	vision_frame_queue.put(frame)
	vision_frame_queue.put(None)
	mock_encoder = MagicMock()
	with patch('facefusion.apis.stream_helper.process_vision_frame', return_value = frame), \
		patch('facefusion.apis.stream_helper.create_vpx_encoder', return_value = mock_encoder), \
		patch('facefusion.apis.stream_helper.encode_vpx_buffer', return_value = None), \
		patch('facefusion.apis.stream_helper.destroy_vpx_encoder') as mock_destroy, \
		patch('facefusion.apis.stream_helper.rtc_store'), \
		patch('facefusion.apis.stream_helper.rtc'):
		run_vp8_encode_loop(vision_frame_queue, 'session-1', (64, 64))
		mock_destroy.assert_called_with(mock_encoder)

	vision_frame_queue = queue.Queue()
	vision_frame_queue.put(frame)
	vision_frame_queue.put(frame)
	vision_frame_queue.put(frame)
	vision_frame_queue.put(None)
	with patch('facefusion.apis.stream_helper.process_vision_frame', return_value = frame), \
		patch('facefusion.apis.stream_helper.create_vpx_encoder', return_value = MagicMock()), \
		patch('facefusion.apis.stream_helper.encode_vpx_buffer', return_value = b'encoded'), \
		patch('facefusion.apis.stream_helper.destroy_vpx_encoder'), \
		patch('facefusion.apis.stream_helper.rtc_store') as mock_rtc_store, \
		patch('facefusion.apis.stream_helper.rtc') as mock_rtc:
		mock_rtc_store.get_rtc_peers.return_value = [ MagicMock() ]
		run_vp8_encode_loop(vision_frame_queue, 'session-1', (64, 64))
		assert mock_rtc.send_video_to_peers.call_count == 3

	vision_frame_queue = queue.Queue()
	vision_frame_queue.put(black_frame)
	with patch('facefusion.apis.stream_helper.create_vpx_encoder', return_value = MagicMock()), \
		patch('facefusion.apis.stream_helper.destroy_vpx_encoder') as mock_destroy, \
		patch('facefusion.apis.stream_helper.rtc') as mock_rtc:
		run_vp8_encode_loop(vision_frame_queue, 'session-1', (64, 64))
		mock_rtc.send_video_to_peers.assert_not_called()
		mock_destroy.assert_called_once()

	vision_frame_queue = queue.Queue()
	vision_frame_queue.put(small_frame)
	vision_frame_queue.put(None)
	with patch('facefusion.apis.stream_helper.process_vision_frame', return_value = large_frame), \
		patch('facefusion.apis.stream_helper.create_vpx_encoder', return_value = MagicMock()) as mock_create, \
		patch('facefusion.apis.stream_helper.encode_vpx_buffer', return_value = b'encoded'), \
		patch('facefusion.apis.stream_helper.destroy_vpx_encoder') as mock_destroy, \
		patch('facefusion.apis.stream_helper.rtc_store') as mock_rtc_store, \
		patch('facefusion.apis.stream_helper.rtc') as mock_rtc:
		mock_rtc_store.get_rtc_peers.return_value = [ MagicMock() ]
		run_vp8_encode_loop(vision_frame_queue, 'session-1', (64, 64))
		assert mock_create.call_count == 2
		assert mock_destroy.call_count == 2
		mock_rtc.send_video_to_peers.assert_called_once()

	vision_frame_queue = queue.Queue()
	vision_frame_queue.put(frame)
	vision_frame_queue.put(None)
	with patch('facefusion.apis.stream_helper.create_vpx_encoder', return_value = None), \
		patch('facefusion.apis.stream_helper.rtc') as mock_rtc:
		run_vp8_encode_loop(vision_frame_queue, 'session-1', (64, 64))
		mock_rtc.send_video_to_peers.assert_not_called()


# TODO: refine test
def test_run_opus_encode_loop() -> None:
	audio_chunk = numpy.zeros(1920, dtype = numpy.float32).tobytes()

	audio_chunk_queue : queue.Queue[Optional[bytes]] = queue.Queue()
	audio_chunk_queue.put(audio_chunk)
	audio_chunk_queue.put(None)
	with patch('facefusion.apis.stream_helper.create_opus_encoder', return_value = MagicMock()), \
		patch('facefusion.apis.stream_helper.encode_opus_buffer', return_value = b'encoded'), \
		patch('facefusion.apis.stream_helper.destroy_opus_encoder'), \
		patch('facefusion.apis.stream_helper.rtc_store') as mock_rtc_store, \
		patch('facefusion.apis.stream_helper.rtc') as mock_rtc:
		mock_rtc_store.get_rtc_peers.return_value = [ MagicMock() ]
		run_opus_encode_loop(audio_chunk_queue, 'session-1')
		mock_rtc.send_audio_to_peers.assert_called_once()
		assert mock_rtc.send_audio_to_peers.call_args[0][2] == 0

	audio_chunk_queue = queue.Queue()
	audio_chunk_queue.put(audio_chunk)
	audio_chunk_queue.put(audio_chunk)
	audio_chunk_queue.put(None)
	with patch('facefusion.apis.stream_helper.create_opus_encoder', return_value = MagicMock()), \
		patch('facefusion.apis.stream_helper.encode_opus_buffer', return_value = b'encoded'), \
		patch('facefusion.apis.stream_helper.destroy_opus_encoder'), \
		patch('facefusion.apis.stream_helper.rtc_store') as mock_rtc_store, \
		patch('facefusion.apis.stream_helper.rtc') as mock_rtc:
		mock_rtc_store.get_rtc_peers.return_value = [ MagicMock() ]
		run_opus_encode_loop(audio_chunk_queue, 'session-1')
		assert mock_rtc.send_audio_to_peers.call_count == 2
		assert mock_rtc.send_audio_to_peers.call_args_list[0][0][2] == 0
		assert mock_rtc.send_audio_to_peers.call_args_list[1][0][2] == 960

	audio_chunk_queue = queue.Queue()
	audio_chunk_queue.put(audio_chunk)
	audio_chunk_queue.put(None)
	with patch('facefusion.apis.stream_helper.create_opus_encoder', return_value = MagicMock()), \
		patch('facefusion.apis.stream_helper.encode_opus_buffer', return_value = b''), \
		patch('facefusion.apis.stream_helper.destroy_opus_encoder'), \
		patch('facefusion.apis.stream_helper.rtc_store'), \
		patch('facefusion.apis.stream_helper.rtc') as mock_rtc:
		run_opus_encode_loop(audio_chunk_queue, 'session-1')
		mock_rtc.send_audio_to_peers.assert_not_called()

	audio_chunk_queue = queue.Queue()
	audio_chunk_queue.put(audio_chunk)
	audio_chunk_queue.put(None)
	with patch('facefusion.apis.stream_helper.create_opus_encoder', return_value = MagicMock()), \
		patch('facefusion.apis.stream_helper.encode_opus_buffer', return_value = None), \
		patch('facefusion.apis.stream_helper.destroy_opus_encoder') as mock_destroy, \
		patch('facefusion.apis.stream_helper.rtc_store'), \
		patch('facefusion.apis.stream_helper.rtc'):
		run_opus_encode_loop(audio_chunk_queue, 'session-1')
		mock_destroy.assert_called_once()

	audio_chunk_queue = queue.Queue()
	audio_chunk_queue.put(b'')
	with patch('facefusion.apis.stream_helper.create_opus_encoder', return_value = MagicMock()), \
		patch('facefusion.apis.stream_helper.destroy_opus_encoder') as mock_destroy, \
		patch('facefusion.apis.stream_helper.rtc') as mock_rtc:
		run_opus_encode_loop(audio_chunk_queue, 'session-1')
		mock_rtc.send_audio_to_peers.assert_not_called()
		mock_destroy.assert_called_once()


# TODO: refine test
def test_run_aom_encode_loop() -> None:
	frame = numpy.full((64, 64, 3), 128, dtype = numpy.uint8)
	small_frame = numpy.full((64, 64, 3), 128, dtype = numpy.uint8)
	large_frame = numpy.full((128, 128, 3), 128, dtype = numpy.uint8)
	black_frame = numpy.zeros((64, 64, 3), dtype = numpy.uint8)

	vision_frame_queue : queue.Queue[Optional[VisionFrame]] = queue.Queue()
	vision_frame_queue.put(frame)
	vision_frame_queue.put(None)
	with patch('facefusion.apis.stream_helper.process_vision_frame', return_value = frame), \
		patch('facefusion.apis.stream_helper.create_aom_encoder', return_value = MagicMock()), \
		patch('facefusion.apis.stream_helper.encode_aom_buffer', return_value = b'encoded'), \
		patch('facefusion.apis.stream_helper.destroy_aom_encoder'), \
		patch('facefusion.apis.stream_helper.rtc_store') as mock_rtc_store, \
		patch('facefusion.apis.stream_helper.rtc') as mock_rtc:
		mock_rtc_store.get_rtc_peers.return_value = [ MagicMock() ]
		run_aom_encode_loop(vision_frame_queue, 'session-1', (64, 64))
		mock_rtc.send_video_to_peers.assert_called_once()

	vision_frame_queue = queue.Queue()
	vision_frame_queue.put(frame)
	vision_frame_queue.put(frame)
	vision_frame_queue.put(frame)
	vision_frame_queue.put(None)
	with patch('facefusion.apis.stream_helper.process_vision_frame', return_value = frame), \
		patch('facefusion.apis.stream_helper.create_aom_encoder', return_value = MagicMock()), \
		patch('facefusion.apis.stream_helper.encode_aom_buffer', return_value = b'encoded'), \
		patch('facefusion.apis.stream_helper.destroy_aom_encoder'), \
		patch('facefusion.apis.stream_helper.rtc_store') as mock_rtc_store, \
		patch('facefusion.apis.stream_helper.rtc') as mock_rtc:
		mock_rtc_store.get_rtc_peers.return_value = [ MagicMock() ]
		run_aom_encode_loop(vision_frame_queue, 'session-1', (64, 64))
		assert mock_rtc.send_video_to_peers.call_count == 3

	vision_frame_queue = queue.Queue()
	vision_frame_queue.put(black_frame)
	with patch('facefusion.apis.stream_helper.create_aom_encoder', return_value = MagicMock()), \
		patch('facefusion.apis.stream_helper.destroy_aom_encoder') as mock_destroy, \
		patch('facefusion.apis.stream_helper.rtc') as mock_rtc:
		run_aom_encode_loop(vision_frame_queue, 'session-1', (64, 64))
		mock_rtc.send_video_to_peers.assert_not_called()
		mock_destroy.assert_called_once()

	vision_frame_queue = queue.Queue()
	vision_frame_queue.put(small_frame)
	vision_frame_queue.put(None)
	with patch('facefusion.apis.stream_helper.process_vision_frame', return_value = large_frame), \
		patch('facefusion.apis.stream_helper.create_aom_encoder', return_value = MagicMock()) as mock_create, \
		patch('facefusion.apis.stream_helper.encode_aom_buffer', return_value = b'encoded'), \
		patch('facefusion.apis.stream_helper.destroy_aom_encoder') as mock_destroy, \
		patch('facefusion.apis.stream_helper.rtc_store') as mock_rtc_store, \
		patch('facefusion.apis.stream_helper.rtc') as mock_rtc:
		mock_rtc_store.get_rtc_peers.return_value = [ MagicMock() ]
		run_aom_encode_loop(vision_frame_queue, 'session-1', (64, 64))
		assert mock_create.call_count == 2
		assert mock_destroy.call_count == 2
		mock_rtc.send_video_to_peers.assert_called_once()

	vision_frame_queue = queue.Queue()
	vision_frame_queue.put(frame)
	vision_frame_queue.put(None)
	with patch('facefusion.apis.stream_helper.create_aom_encoder', return_value = None), \
		patch('facefusion.apis.stream_helper.rtc') as mock_rtc:
		run_aom_encode_loop(vision_frame_queue, 'session-1', (64, 64))
		mock_rtc.send_video_to_peers.assert_not_called()


# TODO: refine test
def test_handle_video_stream() -> None:
	frame = numpy.full((64, 64, 3), 128, dtype = numpy.uint8)
	video_packet = _make_video_packet(frame)
	audio_packet = _make_audio_packet(numpy.zeros(1920, dtype = numpy.float32))

	websocket = _make_handler_websocket([ {'type': 'websocket.receive', 'bytes': video_packet}, {'type': 'websocket.disconnect'} ])
	with patch('facefusion.apis.stream_helper.get_sec_websocket_protocol', return_value = 'proto'), \
		patch('facefusion.apis.stream_helper.extract_access_token', return_value = 'token'), \
		patch('facefusion.apis.stream_helper.session_manager.find_session_id', return_value = 'session-1'), \
		patch('facefusion.apis.stream_helper.session_context.set_session_id'), \
		patch('facefusion.apis.stream_helper.state_manager.get_item', return_value = 30), \
		patch('facefusion.apis.stream_helper.run_aom_encode_loop') as mock_loop, \
		patch('facefusion.apis.stream_helper.run_opus_encode_loop'), \
		patch('facefusion.apis.stream_helper.rtc_store') as mock_rtc:
		asyncio.run(handle_video_stream(websocket))
		websocket.accept.assert_called_once_with(subprotocol = 'proto')
		websocket.send_text.assert_called_once_with('ready')
		websocket.close.assert_called_once()
		mock_rtc.create_rtc_peers.assert_called_once_with('session-1')
		mock_rtc.destroy_rtc_peers.assert_called_once_with('session-1')
		_, loop_session_id, loop_resolution = mock_loop.call_args[0]
		assert loop_session_id == 'session-1'
		assert loop_resolution == (64, 64)

	websocket = _make_handler_websocket([ {'type': 'websocket.receive', 'bytes': video_packet}, {'type': 'websocket.disconnect'} ])
	with patch('facefusion.apis.stream_helper.get_sec_websocket_protocol', return_value = 'proto'), \
		patch('facefusion.apis.stream_helper.extract_access_token', return_value = 'token'), \
		patch('facefusion.apis.stream_helper.session_manager.find_session_id', return_value = None), \
		patch('facefusion.apis.stream_helper.session_context.set_session_id'), \
		patch('facefusion.apis.stream_helper.rtc_store') as mock_rtc:
		asyncio.run(handle_video_stream(websocket))
		websocket.accept.assert_called_once()
		websocket.send_text.assert_not_called()
		mock_rtc.create_rtc_peers.assert_not_called()

	websocket = _make_handler_websocket([ {'type': 'websocket.receive', 'bytes': video_packet}, {'type': 'websocket.receive', 'bytes': audio_packet}, {'type': 'websocket.disconnect'} ])
	with patch('facefusion.apis.stream_helper.get_sec_websocket_protocol', return_value = 'proto'), \
		patch('facefusion.apis.stream_helper.extract_access_token', return_value = 'token'), \
		patch('facefusion.apis.stream_helper.session_manager.find_session_id', return_value = 'session-1'), \
		patch('facefusion.apis.stream_helper.session_context.set_session_id'), \
		patch('facefusion.apis.stream_helper.state_manager.get_item', return_value = 30), \
		patch('facefusion.apis.stream_helper.run_aom_encode_loop'), \
		patch('facefusion.apis.stream_helper.run_opus_encode_loop') as mock_audio_loop, \
		patch('facefusion.apis.stream_helper.rtc_store'):
		asyncio.run(handle_video_stream(websocket))
		audio_queue = mock_audio_loop.call_args[0][0]
		assert create_hash(audio_queue.get_nowait()) == '6d72f0fc'
