import os
import subprocess
import uuid

import cv2
import numpy
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

from facefusion import session_manager, state_manager
from facefusion.apis import asset_store
from facefusion.apis.session_helper import extract_access_token
from facefusion.filesystem import create_directory
from facefusion.node import NODE_REGISTRY, NodeContext, decode_vision_frame, encode_vision_frame
from facefusion.vision import count_video_frame_total, detect_video_fps, read_video_frame

NODES_LOADED = False


def ensure_nodes_loaded() -> None:
	global NODES_LOADED

	if NODES_LOADED:
		return

	NODES_LOADED = True

	import facefusion.face_analyser
	import facefusion.frame_picker

	processor_names =\
	[
		'face_debugger',
		'face_enhancer',
		'face_swapper'
	]

	for processor_name in processor_names:
		try:
			from facefusion.processors.core import load_processor_module

			load_processor_module(processor_name)
		except SystemExit:
			pass


async def list_nodes(request : Request) -> JSONResponse:
	ensure_nodes_loaded()
	nodes = {}

	for name, registered in NODE_REGISTRY.items():
		schema = registered.schema
		nodes[name] =\
		{
			'name' : name,
			'description' : schema.description,
			'inputs' : [ { 'name' : p.name, 'type' : p.type, 'label' : p.label } for p in schema.inputs ],
			'outputs' : [ { 'name' : p.name, 'type' : p.type, 'label' : p.label } for p in schema.outputs ],
			'state_keys' : schema.state_keys
		}

	return JSONResponse(nodes, status_code = HTTP_200_OK)


async def execute_node(request : Request) -> JSONResponse:
	ensure_nodes_loaded()
	node_name = request.path_params.get('node_name')

	if node_name not in NODE_REGISTRY:
		return JSONResponse(
		{
			'message' : 'node not found'
		}, status_code = HTTP_404_NOT_FOUND)

	registered = NODE_REGISTRY[node_name]
	schema = registered.schema
	body = await request.json()
	raw_inputs = body.get('inputs', {})
	state_overrides = body.get('state', {})

	for key in state_overrides:
		if key not in schema.state_keys:
			return JSONResponse(
			{
				'message' : 'state key "' + key + '" not declared for node "' + node_name + '"'
			}, status_code = HTTP_400_BAD_REQUEST)

	# Decode inputs based on port types
	decoded_inputs = {}
	input_port_map = {}

	for port in schema.inputs:
		if port.name not in input_port_map:
			input_port_map[port.name] = []
		input_port_map[port.name].append(port.type)

	for field_name, value in raw_inputs.items():
		port_types = input_port_map.get(field_name, [])

		if isinstance(value, str) and 'video' in port_types and len(value) < 200:
			access_token = extract_access_token(request.scope)
			session_id = session_manager.find_session_id(access_token)
			asset = asset_store.get_asset(session_id, value)

			if asset:
				decoded_inputs[field_name] = asset.get('path')
		elif isinstance(value, str) and 'image' in port_types:
			decoded_inputs[field_name] = decode_vision_frame(value)
		elif isinstance(value, list) and 'image_list' in port_types:
			decoded_inputs[field_name] = [ decode_vision_frame(v) for v in value ]
		else:
			decoded_inputs[field_name] = value

	# Apply state overrides temporarily
	saved_state = {}

	for key, value in state_overrides.items():
		saved_state[key] = state_manager.get_item(key)
		state_manager.set_item(key, value)

	try:
		# Check if any input is a video path
		video_input_name = None
		video_path = None

		for field_name, value in decoded_inputs.items():
			if 'video' in input_port_map.get(field_name, []) and isinstance(value, str):
				video_input_name = field_name
				video_path = value
				break

		output_port_map = {}

		for port in schema.outputs:
			if port.name not in output_port_map:
				output_port_map[port.name] = []
			output_port_map[port.name].append(port.type)

		has_video_output = any('video' in types for types in output_port_map.values())

		# Video processing: loop all frames through the node
		if video_path and has_video_output:
			frame_total = count_video_frame_total(video_path)
			fps = detect_video_fps(video_path)

			if not frame_total or not fps:
				return JSONResponse({ 'message' : 'cannot read video' }, status_code = HTTP_400_BAD_REQUEST)

			first_frame = read_video_frame(video_path, 0)
			height, width = first_frame.shape[:2]
			temp_path = state_manager.get_temp_path()
			create_directory(temp_path)
			output_path = os.path.join(temp_path, uuid.uuid4().hex + '.mp4')

			ffmpeg_process = subprocess.Popen(
			[
				'ffmpeg', '-y',
				'-f', 'rawvideo', '-pix_fmt', 'bgr24',
				'-s', str(width) + 'x' + str(height),
				'-r', str(fps),
				'-i', 'pipe:0',
				'-c:v', 'libx264', '-pix_fmt', 'yuv420p',
				'-movflags', '+faststart',
				'-preset', 'ultrafast',
				output_path
			], stdin = subprocess.PIPE, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)

			frame_result = {}

			for frame_number in range(frame_total):
				frame = read_video_frame(video_path, frame_number)

				if frame is None:
					continue

				frame_inputs = dict(decoded_inputs)
				frame_inputs[video_input_name] = frame

				frame_result = registered.fn(frame_inputs)

				output_frame = frame

				for out_key, out_value in frame_result.items():
					if isinstance(out_value, numpy.ndarray):
						output_frame = out_value
						break

				if output_frame.shape[:2] != (height, width):
					output_frame = cv2.resize(output_frame, (width, height))

				ffmpeg_process.stdin.write(output_frame.tobytes())

			ffmpeg_process.stdin.close()
			ffmpeg_process.wait()

			access_token = extract_access_token(request.scope)
			session_id = session_manager.find_session_id(access_token)
			output_asset = asset_store.create_asset(session_id, 'target', output_path)
			response = {}

			# Return image output from last frame for preview
			for key, value in frame_result.items():
				if isinstance(value, numpy.ndarray):
					response[key] = encode_vision_frame(value)

			# Return video asset ID
			for port in schema.outputs:
				if port.type == 'video' and output_asset:
					response[port.name] = output_asset.get('id')

			return JSONResponse(response, status_code = HTTP_200_OK)

		# Single frame processing
		result = registered.fn(decoded_inputs)

		response = {}

		for key, value in result.items():
			if isinstance(value, numpy.ndarray):
				response[key] = encode_vision_frame(value)
			elif isinstance(value, list) and any(isinstance(v, numpy.ndarray) for v in value):
				response[key] = [ encode_vision_frame(v) for v in value if isinstance(v, numpy.ndarray) ]
			else:
				response[key] = value

		return JSONResponse(response, status_code = HTTP_200_OK)
	except Exception as exception:
		import traceback

		return JSONResponse(
		{
			'message' : str(exception),
			'traceback' : traceback.format_exc()
		}, status_code = HTTP_500_INTERNAL_SERVER_ERROR)
	finally:
		for key, value in saved_state.items():
			state_manager.set_item(key, value)
