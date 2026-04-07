import numpy
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR

from facefusion import state_manager
from facefusion.node import NODE_REGISTRY, NodeContext, decode_vision_frame, encode_vision_frame

NODES_LOADED = False


def ensure_nodes_loaded() -> None:
	global NODES_LOADED

	if NODES_LOADED:
		return

	NODES_LOADED = True

	import facefusion.face_analyser

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
	input_port_types = { p.name: p.type for p in schema.inputs }

	for field_name, value in raw_inputs.items():
		port_type = input_port_types.get(field_name, '')

		if port_type == 'image' and isinstance(value, str):
			decoded_inputs[field_name] = decode_vision_frame(value)
		elif port_type == 'image_list' and isinstance(value, list):
			decoded_inputs[field_name] = [ decode_vision_frame(v) for v in value ]
		else:
			decoded_inputs[field_name] = value

	# Apply state overrides temporarily
	saved_state = {}

	for key, value in state_overrides.items():
		saved_state[key] = state_manager.get_item(key)
		state_manager.set_item(key, value)

	try:
		result = registered.fn(decoded_inputs)

		# Encode outputs based on port types
		output_port_types = { p.name: p.type for p in schema.outputs }
		response = {}

		for key, value in result.items():
			port_type = output_port_types.get(key, '')

			if port_type == 'image' and isinstance(value, numpy.ndarray):
				response[key] = encode_vision_frame(value)
			elif port_type == 'image_list' and isinstance(value, list):
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
