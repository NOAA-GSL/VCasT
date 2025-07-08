"""
Processing Module for VCasT
---------------------------
This module contains functionality for parallel computation and data interpolation.

Modules:
- parallel_processing.py: Handles multiprocessing execution for data processing.
- interpolation.py: Implements interpolation techniques for data transformation.
- postprocessing.py: Implements the class StatisticalSignificance.

Available Functions/Classes:
- process_in_parallel: Runs statistical computation in parallel (requires processing extras).
- interpolate_to_target_grid: Interpolates data to a target grid (requires processing extras).
- StatiscalSignificance: Performs statistical significance testing (requires processing extras).
"""

try:
    from .interpolation import interpolate_to_target_grid
except ImportError:
    interpolate_to_target_grid = None

try:
    from .parallel_processing import process_in_parallel
except ImportError:
    process_in_parallel = None

try:
    from .postprocessing import StatiscalSignificance
except ImportError:
    StatiscalSignificance = None

__all__ = [
    "process_in_parallel",
    "interpolate_to_target_grid",
    "StatiscalSignificance"
]
