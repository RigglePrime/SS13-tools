from colorama import init as colorama_init

from .__version__ import __version__

colorama_init()

VERSION = __version__

__all__ = [
    'slur_detector',
    'centcom',
    'byond',
    'log_downloader'
]

del colorama_init
