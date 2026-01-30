"""rename_project - A tool for renaming projects."""

import logging

__version__ = "0.1.0"
__all__ = ["__version__"]

# Library pattern: add NullHandler to prevent "No handler found" warnings
logging.getLogger(__name__).addHandler(logging.NullHandler())
