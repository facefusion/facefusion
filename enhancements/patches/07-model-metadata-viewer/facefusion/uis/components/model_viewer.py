"""
Override for ModelViewerPanel to display ONNX graph, layers,
and input/output shapes.
"""

from facefusion.uis.components.model_viewer import ModelViewerPanel as BasePanel
from facefusion.model_helper import EnhancedModelHelper

class EnhancedModelViewerPanel(BasePanel):
    """
    UI panel showing model graph and tensor shapes.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = EnhancedModelHelper()
        # TODO: add controls to load a model path

    def load_model(self, model_path: str):
        """
        Load model and render its graph and shapes.
        """
        info = self.helper.get_graph_info(model_path)
        # Assume BasePanel has methods to display graph and shapes
        self.display_graph(info["nodes"])
        self.display_shapes(info["input_shapes"], info["output_shapes"])
