import asyncio
import threading
from typing import List

import cv2
import numpy
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR
from starlette.websockets import WebSocket

from facefusion import rtc, session_context, session_manager, state_manager
from facefusion.apis.api_helper import get_sec_websocket_protocol
from facefusion.apis.session_helper import extract_access_token
from facefusion.apis.stream_helper import calculate_stream_bitrate, forward_stream_frames, run_video_pipeline
from facefusion.ffmpeg import spawn_stream
from facefusion.streamer import process_vision_frame
from facefusion.types import RtcPeer
from facefusion.vision import detect_video_fps, detect_video_resolution


async def websocket_stream(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)
	access_token = extract_access_token(websocket.scope)
	session_id = session_manager.find_session_id(access_token)

	session_context.set_session_id(session_id)
	source_paths = state_manager.get_item('source_paths')

	await websocket.accept(subprotocol = subprotocol)

	if source_paths:
		try:
			image_buffer = await websocket.receive_bytes()
			target_vision_frame = cv2.imdecode(numpy.frombuffer(image_buffer, numpy.uint8), cv2.IMREAD_COLOR)

			if numpy.any(target_vision_frame):
				temp_vision_frame = process_vision_frame(target_vision_frame)
				is_success, output_vision_frame = cv2.imencode('.jpg', temp_vision_frame)

				if is_success:
					await websocket.send_bytes(output_vision_frame.tobytes())

		except Exception:
			pass
		return

	await websocket.close()


async def handle_whep_offer(request : Request) -> Response:
	access_token = extract_access_token(request.scope)
	session_id = session_manager.find_session_id(access_token)

	if session_id:
		session_context.set_session_id(session_id)
		body = await request.json()
		sdp_offer = body.get('sdp')

		if sdp_offer and isinstance(sdp_offer, str):
			sessions = request.app.state.rtc_sessions # TODO: improve rtc sessions
			stream_path = '/' + session_id

			if stream_path not in sessions:
				sessions[stream_path] = []

			peers = sessions[stream_path]
			sdp_answer = await asyncio.to_thread(rtc.handle_whep_offer, peers, sdp_offer)

			if sdp_answer:
				target_path = state_manager.get_item('target_path')

				if target_path:
					asyncio.create_task(stream_target_video(peers, target_path))

				return JSONResponse(
				{
					'sdp': sdp_answer,
					'type': 'answer'
				})

	return Response(status_code = HTTP_500_INTERNAL_SERVER_ERROR)


async def stream_target_video(peers : List[RtcPeer], target_path : str) -> None:
	wait_limit = asyncio.get_running_loop().time() + 2.0

	while not rtc.is_peer_connected(peers) and asyncio.get_running_loop().time() < wait_limit:
		await asyncio.sleep(0.1)

	video_fps = detect_video_fps(target_path)
	video_resolution = detect_video_resolution(target_path)

	if video_resolution:
		stream_pipe = spawn_stream(video_resolution, int(video_fps), calculate_stream_bitrate(video_resolution))
		reader_thread = threading.Thread(target = forward_stream_frames, args = (peers, stream_pipe), daemon = True)
		reader_thread.start()
		await asyncio.to_thread(run_video_pipeline, peers, stream_pipe, target_path, video_fps)
