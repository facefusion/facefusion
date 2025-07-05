#!/usr/bin/env python3
"""
apply_patch07_full.py

Scaffolds and implements Patch 07: Model & Metadata Viewer Enhancements.

This single script will:
  1. Create the patch directory and README.
  2. Write override implementations for:
     - EnhancedModelViewerPanel (model_viewer.py)
     - EnhancedMetadataViewerPanel (metadata_viewer.py)
     - EnhancedModelHelper (model_helper.py)
  3. Create the pytest suite.
  4. Update patch_log.txt.

Usage:
    python apply_patch07_full.py --root "C:\\facefusion" [--verbose]
"""

import argparse
import logging
from pathlib import Path
import textwrap

FILES = {
    # README
    "enhancements/patches/07-model-metadata-viewer/README.md": textwrap.dedent("""\
        # Patch 07: Model & Metadata Viewer Enhancements

        **Goal:**
        Provide UI panels to inspect ML model graphs, layers, input/output shapes,
        and to view file-embedded metadata side-by-side.

        **Touchpoints:**
        - Override `facefusion/uis/components/model_viewer.py`
        - Override `facefusion/uis/components/metadata_viewer.py`
        - Override `facefusion/model_helper.py`
        - Add tests under `tests/test_model_metadata_viewer.py`
    """),

    # Initial patch log
    "enhancements/patches/07-model-metadata-viewer/patch_log.txt": textwrap.dedent("""\
        Patch 07:
        - Scaffolded Model & Metadata Viewer Enhancements patch directory.
        - Wrote EnhancedModelViewerPanel, EnhancedMetadataViewerPanel, and EnhancedModelHelper.
        - Added tests for override modules.
    """),

    # Override: model_viewer.py
    "enhancements/patches/07-model-metadata-viewer/facefusion/uis/components/model_viewer.py": textwrap.dedent("""\
        \"\"\"
        Override for ModelViewerPanel to display ONNX graph, layers,
        and input/output shapes.
        \"\"\"

        from facefusion.uis.components.model_viewer import ModelViewerPanel as BasePanel
        from facefusion.model_helper import EnhancedModelHelper

        class EnhancedModelViewerPanel(BasePanel):
            \"\"\"
            UI panel showing model graph and tensor shapes.
            \"\"\"
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.helper = EnhancedModelHelper()
                # TODO: add controls to load a model path

            def load_model(self, model_path: str):
                \"\"\"
                Load model and render its graph and shapes.
                \"\"\"
                info = self.helper.get_graph_info(model_path)
                # Assume BasePanel has methods to display graph and shapes
                self.display_graph(info["nodes"])
                self.display_shapes(info["input_shapes"], info["output_shapes"])
    """),

    # Override: metadata_viewer.py
    "enhancements/patches/07-model-metadata-viewer/facefusion/uis/components/metadata_viewer.py": textwrap.dedent("""\
        \"\"\"
        Override for MetadataViewerPanel to show file-embedded metadata.
        \"\"\"

        from facefusion.uis.components.metadata_viewer import MetadataViewerPanel as BasePanel
        from facefusion.model_helper import EnhancedModelHelper

        class EnhancedMetadataViewerPanel(BasePanel):
            \"\"\"
            UI panel showing embedded metadata for media or model files.
            \"\"\"
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.helper = EnhancedModelHelper()
                # TODO: add controls to select media/model file

            def load_metadata(self, file_path: str):
                \"\"\"
                Load and render metadata dictionary.
                \"\"\"
                data = self.helper.get_metadata(file_path)
                self.display_metadata(data)
    """),

    # Override: model_helper.py
    "enhancements/patches/07-model-metadata-viewer/facefusion/model_helper.py": textwrap.dedent("""\
        \"\"\"
        Override ModelHelper to extract graph and metadata information.
        \"\"\"

        import onnx
        from facefusion.model_helper import ModelHelper as BaseHelper

        class EnhancedModelHelper(BaseHelper):
            \"\"\"
            Adds methods to retrieve graph node types and tensor shapes,
            and load file metadata.
            \"\"\"
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
    """),

    # Test suite
    "enhancements/patches/07-model-metadata-viewer/tests/test_model_metadata_viewer.py": textwrap.dedent("""\
        \"\"\"
        Tests for Model & Metadata Viewer Enhancements overrides.
        \"\"\"

        import importlib

        def test_model_viewer_override():
            mod = importlib.import_module('facefusion.uis.components.model_viewer')
            assert 'EnhancedModelViewerPanel' in dir(mod)

        def test_metadata_viewer_override():
            mod = importlib.import_module('facefusion.uis.components.metadata_viewer')
            assert 'EnhancedMetadataViewerPanel' in dir(mod)

        def test_model_helper_override():
            mod = importlib.import_module('facefusion.model_helper')
            assert 'EnhancedModelHelper' in dir(mod)
    """),
}


def apply_patch(root: Path):
    """
    Create and write all override and test files for Patch 07.
    """
    for rel_path, content in FILES.items():
        file_path = root / Path(rel_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        logging.info(f"Wrote {file_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Apply Patch 07 full scaffold & implementation."
    )
    parser.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Path to FaceFusion project root (e.g., C:\\facefusion)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

    project_root = args.root.resolve()
    if not (project_root / "facefusion").is_dir():
        logging.error("Invalid FaceFusion root: %s", project_root)
        return

    apply_patch(project_root)
    logging.info("Patch 07 full implementation complete.")


if __name__ == "__main__":
    main()
