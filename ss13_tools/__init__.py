from colorama import init as colorama_init

from .__version__ import __version__

# Commented out for now since it throws an exception on load
# This is bad as users mostly double click to run, and the window
# immediately closes. Not sure hot to refactor this yet
# from . import slur_detector
from . import centcom
from . import byond
from . import log_downloader

colorama_init()

VERSION = __version__

__all__ = [
    # 'slur_detector',
    'centcom',
    'byond',
    'log_downloader'
]

del colorama_init
