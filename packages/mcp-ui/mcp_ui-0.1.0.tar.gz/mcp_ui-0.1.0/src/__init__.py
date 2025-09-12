from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("mcp-ui")
except PackageNotFoundError:
    # fallback for local dev without install
    __version__ = "0.0.0"

from .core import * 
