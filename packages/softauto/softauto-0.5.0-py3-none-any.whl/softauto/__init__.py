from importlib.metadata import version, PackageNotFoundError
from .autorun import AutoRun, autorun

try:
    __version__ = version("softauto")
except PackageNotFoundError:
    __version__ = "0.5.0"

__all__ = ["AutoRun", "autorun", "__version__"]
