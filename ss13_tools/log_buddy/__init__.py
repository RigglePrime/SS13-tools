from colorama import init as colorama_init

from .log import Log, LogType
from .log_parser import LogFile
from .__main__ import main  # noqa: F401


colorama_init()

__all__ = [
    'LogFile',
    'Log',
    'LogType'
]

del colorama_init
