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

try:
    from .file_checker import FileChecker
except ImportError:
    FileChecker = None

try:
    from .preprocess import Preprocessor
except ImportError:
    Preprocessor = None

__all__ = [
    "FileChecker",
    "Preprocessor",
]
