from .__version__ import __version__
from .ckey_log_downloader import CkeyLogDownloader
from .round_log_downloader import RoundLogDownloader
from scrubby import RoundData

import sys

from colorama import init as colorama_init
import asyncio

colorama_init()

if sys.platform == "win32":
    # This fixes a lot of runtime errors.
    # It's supposed to be fixed but oh well.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

version = __version__

__all__ = [
    'CkeyLogDownloader',
    'RoundLogDownloader',
    'RoundData'
]
