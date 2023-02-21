from colorama import init as colorama_init

from .slur_detector import SlurDetector
from .__main__ import main  # noqa: F401

colorama_init()

__all__ = [
    'SlurDetector'
]
