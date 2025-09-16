"""
Jymkit has been renamed to Jaxnasium.

This package provides backward compatibility by mapping all jymkit imports to jaxnasium.
Please consider migrating to the jaxnasium package directly.
"""

import sys
import warnings

warnings.warn(
    "jymkit has been renamed to jaxnasium. Please install and use the jaxnasium package instead.",
    DeprecationWarning,
)

import jaxnasium
from jaxnasium import *

# Make jaxnasium available as jymkit for backward compatibility
sys.modules[__name__] = jaxnasium
