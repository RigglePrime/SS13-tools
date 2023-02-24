from colorama import init as colorama_init

from .auth import Passport, interactive, is_authenticated, save_passport, load_passport, create_with_token, PASSPORT
from .__main__ import main  # noqa: F401


colorama_init()
load_passport()

__all__ = [
    'Passport',
    'interactive',
    'is_authenticated',
    'save_passport',
    'load_passport',
    'create_with_token',
    'PASSPORT'
]

del colorama_init
