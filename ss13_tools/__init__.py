from .__version__ import __version__

from colorama import init as colorama_init

colorama_init()

version = __version__

__all__ = [
    'slur_detector',
    'centcom',
    'byond_tools'
]
