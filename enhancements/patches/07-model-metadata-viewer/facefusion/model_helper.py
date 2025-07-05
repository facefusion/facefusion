"""
Override ModelHelper to extract graph and metadata information.
"""

import onnx
from facefusion.model_helper import ModelHelper as BaseHelper

class EnhancedModelHelper(BaseHelper):
    """
    Adds methods to retrieve graph node types and tensor shapes,
    and load file metadata.
    """
    @staticmethod
    def get_graph_info(model_path: str) -> dict:
        model = onnx.load(model_path)
        nodes = [n.op_type for n in model.graph.node]
        input_shapes = [
            tuple(dim.dim_value for dim in inp.type.tensor_type.shape.dim)
            for inp in model.graph.input
        ]
        output_shapes = [
            tuple(dim.dim_value for dim in out.type.tensor_type.shape.dim)
            for out in model.graph.output
        ]
        return {
            "nodes": nodes,
            "input_shapes": input_shapes,
            "output_shapes": output_shapes
        }

    @staticmethod
    def get_metadata(file_path: str) -> dict:
        # Fallback to BaseHelper if available, else empty dict
        try:
            return BaseHelper.get_metadata(file_path)
        except AttributeError:
            return {}
