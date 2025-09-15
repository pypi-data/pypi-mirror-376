"""
polarion_rest_client (high-level layer)

Exports:
- __version__     : installed distribution version
- PolarionClient  : HL wrapper holding the generated client
- get_env_vars()  : read env vars and return kwargs for PolarionClient
"""

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("polarion-rest-client")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0"

from .client import PolarionClient
from .session import get_env_vars

__all__ = ["__version__", "PolarionClient", "get_env_vars"]

