"""
Raspberry Pi package.
"""
import os
import json
from .constants import ASSETS_DIR

with open(os.path.join(ASSETS_DIR, "metadata.json")) as f:
    metadata = json.load(f)

__title__ = metadata["__title__"]
__description__ = metadata["__description__"]
__version__ = metadata["__version__"]
__lead__ = metadata["__lead__"]
__email__ = metadata["__email__"]
__url__ = metadata["__url__"]

__all__ = [
    "__title__",
    "__description__",
    "__version__",
    "__lead__",
    "__email__",
    "__url__",
]
