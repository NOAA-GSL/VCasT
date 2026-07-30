"""
VCasT Preprocess Module
-----------------------
This module handles file operations and preprocessing.

Modules:
- file_checker.py: Checks file formats and ensures compatibility.
- preprocess.py: Handles data preprocessing and formatting.

Available Classes:
- FileChecker: Identifies file formats and validates input data (requires pygrib).
- Preprocessor: Processes input files and prepares them for analysis.
"""

import logging

try:
    from .file_checker import FileChecker
except ImportError as e:
    logging.warning(
        "vcast.preprocess.FileChecker unavailable (%s). Install the "
        "'preprocess'/'processing'/'all' extras, and make sure the "
        "eccodes system library pygrib depends on is installed "
        "(e.g. `apt-get install libeccodes-dev` on Debian/Ubuntu).", e
    )
    FileChecker = None

try:
    from .preprocess import Preprocessor
except ImportError as e:
    logging.warning(
        "vcast.preprocess.Preprocessor unavailable (%s). Install the "
        "'preprocess'/'processing'/'all' extras, and make sure the "
        "eccodes system library pygrib depends on is installed "
        "(e.g. `apt-get install libeccodes-dev` on Debian/Ubuntu).", e
    )
    Preprocessor = None

__all__ = [
    "FileChecker",
    "Preprocessor",
]
