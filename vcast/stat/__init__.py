"""
Statistical Processing Module for VCasT
---------------------------------------
This module provides tools for handling statistical calculations and verification metrics.

Modules:
- `constants.py`: Defines constants used across the statistical calculations.
- `stat_handler.py`: Handles statistical processing, filtering, and aggregation.
- `stats.py`: Implements specific statistical computations.
"""

from .constants import *
from .stat_handler import ReadStat
from .stats import *

__all__ = ["ReadStat"]
