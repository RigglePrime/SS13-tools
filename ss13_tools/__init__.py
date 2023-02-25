from colorama import init as colorama_init

from .__version__ import __version__

from . import slur_detector
from . import centcom
from . import byond
from . import log_downloader

colorama_init()

VERSION = __version__

__all__ = [
    'slur_detector',
    'centcom',
    'byond',
    'log_downloader'
]

del colorama_init
