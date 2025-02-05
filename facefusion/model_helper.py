from functools import lru_cache

import onnx

from facefusion.types import ModelInitializer


@lru_cache(maxsize = None)
def get_static_model_initializer(model_path : str) -> ModelInitializer:
	model = onnx.load(model_path)
	return onnx.numpy_helper.to_array(model.graph.initializer[-1])
