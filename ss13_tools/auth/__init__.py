from colorama import init as colorama_init

from .tg import Passport, interactive, is_authenticated, save_passport, \
                  load_passport, create_from_token, get_auth_headers, seconds_left


colorama_init()
load_passport()

__all__ = [
    'Passport',
    'interactive',
    'is_authenticated',
    'save_passport',
    'load_passport',
    'create_from_token',
    'seconds_left',
    'get_auth_headers',
]

del colorama_init
