import base64
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Type

import cv2
import numpy
from numpy.typing import NDArray


@dataclass
class NodePort:
	name : str
	type : str  # 'image', 'json', 'faces'
	label : str = ''


@dataclass
class NodeSchema:
	name : str
	inputs : List[NodePort]
	outputs : List[NodePort]
	state_keys : List[str]
	description : str = ''


@dataclass
class RegisteredNode:
	schema : NodeSchema
	fn : Callable


NODE_REGISTRY : Dict[str, RegisteredNode] = {}


class NodeContext:
	def __init__(self, state : Dict[str, Any]) -> None:
		self._state = dict(state)

	def get_item(self, key : str) -> Any:
		value = self._state.get(key)

		if value is None:
			from facefusion import state_manager

			value = state_manager.get_item(key)

		return value

	def __getitem__(self, key : str) -> Any:
		return self.get_item(key)

	def __contains__(self, key : str) -> bool:
		return key in self._state

	def to_dict(self) -> Dict[str, Any]:
		return dict(self._state)


def node(name : str, inputs : List[NodePort], outputs : List[NodePort], state_keys : List[str], description : str = '') -> Callable:
	def decorator(fn : Callable) -> Callable:
		schema = NodeSchema(
			name = name,
			inputs = inputs,
			outputs = outputs,
			state_keys = state_keys,
			description = description
		)

		@wraps(fn)
		def wrapper(inputs_dict : Dict[str, Any], ctx : Optional[NodeContext] = None) -> Dict[str, Any]:
			if ctx is None:
				from facefusion import state_manager

				state_snapshot = { key: state_manager.get_item(key) for key in state_keys }
				ctx = NodeContext(state_snapshot)
			return fn(inputs_dict, ctx)

		wrapper.__node_schema__ = schema
		NODE_REGISTRY[name] = RegisteredNode(schema = schema, fn = wrapper)
		return wrapper

	return decorator


def get_node(name : str) -> Optional[RegisteredNode]:
	return NODE_REGISTRY.get(name)


def get_all_nodes() -> Dict[str, RegisteredNode]:
	return NODE_REGISTRY


def decode_vision_frame(b64_string : str) -> NDArray[Any]:
	image_bytes = base64.b64decode(b64_string)
	return cv2.imdecode(numpy.frombuffer(image_bytes, numpy.uint8), cv2.IMREAD_COLOR)


def encode_vision_frame(frame : NDArray[Any], fmt : str = '.jpg') -> str:
	_, buffer = cv2.imencode(fmt, frame)
	return base64.b64encode(buffer.tobytes()).decode('utf-8')
