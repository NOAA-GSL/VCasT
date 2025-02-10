"""
VCasT: Verification and Forecast Evaluation Tool
------------------------------------------------
VCasT is a library designed for weather model verification, providing tools for:
- Statistical processing
- Data handling and preprocessing
- Parallel computation
- Plot generation for visualization

Modules:
- `io`: Handles input/output operations, config loading, and file checks.
- `plot`: Implements plotting functions including performance and Taylor diagrams.
- `processing`: Contains interpolation and parallel data processing.
- `stat`: Provides statistical calculations and data aggregation.

"""

# Importing core functionalities for external use
from .io import ConfigLoader, OutputFileHandler, FileChecker, Preprocessor
from .plot import Plot
from .processing import process_in_parallel, interpolate_to_target_grid
from .stat import ReadStat

__all__ = [
    "ConfigLoader",
    "OutputFileHandler",
    "FileChecker",
    "Preprocessor",
    "Plot",
    "process_in_parallel",
    "interpolate_to_target_grid",
    "ReadStat"
]
