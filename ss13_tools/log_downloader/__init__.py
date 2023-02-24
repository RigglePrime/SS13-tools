import sys
import asyncio

from colorama import init as colorama_init

from .ckey import CkeyLogDownloader
from .round import RoundLogDownloader
from ..scrubby import RoundData

colorama_init()

if sys.platform == "win32":
    # This fixes a lot of runtime errors.
    # It's supposed to be fixed but oh well.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

__all__ = [
    'CkeyLogDownloader',
    'RoundLogDownloader',
    'RoundData'
]

del colorama_init
