from colorama import init as colorama_init

from .key_tools import canonicalize, user_exists
from .__main__ import main  # noqa: F401

colorama_init()

__all__ = [
    'canonicalize',
    'user_exists'
]

del colorama_init
