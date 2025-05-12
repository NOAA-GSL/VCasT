# preprocess/__init__.py

"""
VCasT I/O Module
----------------
This module handles file operations, and preprocessing.

Modules:
- file_checker.py: Checks file formats and ensures compatibility.
- preprocess.py: Handles data preprocessing and formatting.

Available Classes:
- FileChecker: Identifies file formats and validates input data.
- Preprocessor: Processes input files and prepares them for analysis.
"""

from .file_checker import FileChecker
from .preprocess import Preprocessor

__all__ = [
    "FileChecker",
    "Preprocessor",
]
