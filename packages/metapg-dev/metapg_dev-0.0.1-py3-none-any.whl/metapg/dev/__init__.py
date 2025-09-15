"""metapg.dev: Development tools and testing utilities for metapg.

This package provides development dependencies and testing utilities
for the metapg project to ensure consistent development environments.
"""

__version__ = "0.0.1"
__author__ = "Darwin Monroy"
__email__ = "darwin@ideatives.com"

# Import testing utilities for easy access
from .testing import DatabaseTestConfig, drop_test_databases, setup_test_databases

__all__ = [
    "DatabaseTestConfig",
    "__author__",
    "__email__",
    "__version__",
    "drop_test_databases",
    "setup_test_databases",
]
