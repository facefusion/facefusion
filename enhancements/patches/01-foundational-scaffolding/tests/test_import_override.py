"""
Test that the enhancements folder is prepended to sys.path,
ensuring our shadow modules take precedence.
"""

import sys
import os

def test_enhancements_path_precedence():
    # The first entry in sys.path should be the enhancements root
    first_entry = sys.path[0]
    assert os.path.basename(first_entry) == "enhancements", (
        f"Expected first sys.path entry to be 'enhancements', got {first_entry}"
    )
