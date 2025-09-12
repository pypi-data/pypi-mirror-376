import importlib.metadata

__version__ = importlib.metadata.version("xcolleapi")

from .gcolle import GcolleAPI
from .pcolle import PcolleAPI

__all__ = ["GcolleAPI", "PcolleAPI"]
