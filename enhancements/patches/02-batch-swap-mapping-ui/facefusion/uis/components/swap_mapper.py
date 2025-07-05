"""
Batch Swap Mapping UI override.
"""

from facefusion.uis.components.swap_mapper import SwapMapper

class BatchSwapMapper(SwapMapper):
    """
    Extended SwapMapper supporting batch source→target assignment.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mappings = []

    def load_mappings(self, mapping_file: str) -> None:
        import json, csv
        from pathlib import Path
        path = Path(mapping_file)
        if path.suffix.lower() == ".json":
            self.mappings = json.loads(path.read_text())
        elif path.suffix.lower() == ".csv":
            with path.open(newline="") as f:
                reader = csv.reader(f)
                self.mappings = [tuple(row) for row in reader]
        else:
            raise ValueError(f"Unsupported mapping file: {path.suffix}")

    def get_mappings(self):
        return self.mappings
