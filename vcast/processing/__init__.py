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

import logging

_MISSING_EXTRA_HINT = (
    "Install the 'processing'/'all' extras, and make sure the eccodes "
    "system library pygrib depends on is installed (e.g. "
    "`apt-get install libeccodes-dev` on Debian/Ubuntu)."
)

try:
    from .interpolation import interpolate_to_target_grid
except ImportError as e:
    logging.warning("vcast.processing.interpolate_to_target_grid unavailable (%s). %s",
                     e, _MISSING_EXTRA_HINT)
    interpolate_to_target_grid = None

try:
    from .parallel_processing import process_in_parallel
except ImportError as e:
    logging.warning("vcast.processing.process_in_parallel unavailable (%s). %s",
                     e, _MISSING_EXTRA_HINT)
    process_in_parallel = None

try:
    from .postprocessing import StatiscalSignificance
except ImportError as e:
    logging.warning("vcast.processing.StatiscalSignificance unavailable (%s). %s",
                     e, _MISSING_EXTRA_HINT)
    StatiscalSignificance = None

__all__ = [
    "process_in_parallel",
    "interpolate_to_target_grid",
    "StatiscalSignificance"
]
