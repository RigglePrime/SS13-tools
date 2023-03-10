import sys
import asyncio

from colorama import init as colorama_init

from .ckey import CkeyLogDownloader
from .round import RoundLogDownloader, RoundListLogDownloader
from ..scrubby import PlayerRoundData

colorama_init()

if sys.platform == "win32":
    # This fixes a lot of runtime errors.
    # It's supposed to be fixed but oh well.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

__all__ = [
    'CkeyLogDownloader',
    'RoundLogDownloader',
    'RoundListLogDownloader',
    'PlayerRoundData',
]

del colorama_init
