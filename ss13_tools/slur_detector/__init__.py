from colorama import init as colorama_init

from .slur_detector import SlurDetector

colorama_init()

__all__ = [
    'SlurDetector'
]

del colorama_init
