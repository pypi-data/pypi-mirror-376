# flake8: noqa

# Set version ----
from importlib.metadata import version as _v, PackageNotFoundError as _PNF

try:
	__version__ = _v("google_ngrams")
except _PNF:  # Fallback when running from source without installed metadata
	__version__ = "0.0.0"

del _v

# Imports ----

from .ngrams import google_ngram

from .vnc import TimeSeries

__all__ = ['google_ngram', 'TimeSeries']