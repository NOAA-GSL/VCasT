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
from .io import ConfigLoader, OutputFileHandler
from .preprocess import FileChecker, Preprocessor
from .processing import process_in_parallel, interpolate_to_target_grid, StatiscalSignificance

try:
    from .metstat import ReadStat
except ImportError:
    ReadStat = None

try:
    from .plot import BasePlot, LinePlot, Reliability, PerformanceDiagram
except ImportError:
    BasePlot = LinePlot = Reliability = PerformanceDiagram = None

try:
    from .agg import Aggregation
except ImportError:
    Aggregation = None

__all__ = [
    "ConfigLoader",
    "OutputFileHandler",
    "FileChecker",
    "Preprocessor",
    "process_in_parallel",
    "interpolate_to_target_grid",
    "ReadStat",
    "BasePlot", 
    "LinePlot", 
    "Reliability", 
    "PerformanceDiagram",
    "StatiscalSignificance",
    "Aggregation"
]
