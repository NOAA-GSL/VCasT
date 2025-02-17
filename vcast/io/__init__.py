# io/__init__.py

"""
VCasT I/O Module
----------------
This module handles configuration loading, file operations, and preprocessing.

Modules:
- config_loader.py: Loads and parses YAML configuration files.
- output_file_handler.py: Manages output file creation and writing.
- file_checker.py: Checks file formats and ensures compatibility.
- preprocess.py: Handles data preprocessing and formatting.

Available Classes:
- ConfigLoader: Loads and structures configuration parameters from YAML.
- OutputFileHandler: Handles opening, writing, and closing of output files.
- FileChecker: Identifies file formats and validates input data.
- Preprocessor: Processes input files and prepares them for analysis.
"""

from .config_loader import ConfigLoader
from .output_file_handler import OutputFileHandler
from .file_checker import FileChecker
from .preprocess import Preprocessor

__all__ = [
    "ConfigLoader",
    "OutputFileHandler",
    "FileChecker",
    "Preprocessor",
]
