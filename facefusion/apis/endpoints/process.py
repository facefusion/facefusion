import os
import uuid
from time import time
from typing import Optional

from starlette.websockets import WebSocket

from facefusion import ffmpeg, process_manager, session_context, session_manager, state_manager
from facefusion.apis.api_helper import get_sec_websocket_protocol
from facefusion.apis.endpoints.session import extract_access_token
from facefusion.filesystem import create_directory, remove_file
from facefusion.workflows import image_to_image


def save_image_bytes(image_bytes : bytes, temp_path : str, file_extension : str) -> str:
	raw_path = os.path.join(temp_path, str(uuid.uuid4()) + file_extension)

	with open(raw_path, 'wb') as raw_file:
		raw_file.write(image_bytes)

	return raw_path


def sanitize_upload(raw_path : str, temp_path : str, file_extension : str) -> Optional[str]:
	target_path = os.path.join(temp_path, str(uuid.uuid4()) + file_extension)

	process_manager.start()
	sanitized = ffmpeg.sanitize_image(raw_path, target_path)
	process_manager.end()
	remove_file(raw_path)

	if sanitized:
		return target_path
	return None


def process_target(target_path : str, output_path : str) -> bool:
	state_manager.set_item('target_path', target_path)
	state_manager.set_item('output_path', output_path)
	state_manager.set_item('workflow', 'image-to-image')

	error_code = image_to_image.process(time())
	remove_file(target_path)

	return error_code == 0


async def websocket_process_image(websocket : WebSocket) -> None:
	subprotocol = get_sec_websocket_protocol(websocket.scope)
	access_token = extract_access_token(websocket.scope)
	session_id = session_manager.find_session_id(access_token)

	session_context.set_session_id(session_id)
	source_paths = state_manager.get_item('source_paths')

	await websocket.accept(subprotocol = subprotocol)

	if source_paths:
		temp_path = state_manager.get_temp_path()
		create_directory(temp_path)

		try:
			while True:
				image_bytes = await websocket.receive_bytes()
				raw_path = save_image_bytes(image_bytes, temp_path, '.jpg')
				target_path = sanitize_upload(raw_path, temp_path, '.jpg')

				if target_path:
					output_path = os.path.join(temp_path, str(uuid.uuid4()) + '.jpg')

					if process_target(target_path, output_path):
						with open(output_path, 'rb') as output_file:
							await websocket.send_bytes(output_file.read())

						remove_file(output_path)

		except Exception:
			pass
		return

	await websocket.close(code = 1008)
