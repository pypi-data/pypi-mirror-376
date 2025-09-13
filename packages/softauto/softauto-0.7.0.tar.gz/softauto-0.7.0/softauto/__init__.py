from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("softauto")
except PackageNotFoundError:
    __version__ = "0.7.0"

from .advisor import Advisor, advise
from .runner import Runner, autorun

__all__ = ["__version__", "Advisor", "advise", "Runner", "autorun"]
