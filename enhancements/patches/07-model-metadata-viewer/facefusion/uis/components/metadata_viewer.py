"""
Override for MetadataViewerPanel to show file-embedded metadata.
"""

from facefusion.uis.components.metadata_viewer import MetadataViewerPanel as BasePanel
from facefusion.model_helper import EnhancedModelHelper

class EnhancedMetadataViewerPanel(BasePanel):
    """
    UI panel showing embedded metadata for media or model files.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = EnhancedModelHelper()
        # TODO: add controls to select media/model file

    def load_metadata(self, file_path: str):
        """
        Load and render metadata dictionary.
        """
        data = self.helper.get_metadata(file_path)
        self.display_metadata(data)
