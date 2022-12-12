from .constants import BYOND_MEMBERS_URL

from string import ascii_lowercase, digits
from urllib.parse import quote

import requests as req


def canonicalize(key: str) -> str:
    return ''.join([c for c in key.lower() if c in ascii_lowercase + digits + '@'])


def user_exists(key: str) -> bool:
    ckey = canonicalize(key)
    # canonicalize should make it url safe but just in case let's also use quote
    r = req.get(BYOND_MEMBERS_URL.format(ckey=quote(ckey)))
    # The issue here is that when a user doesn't exist, the website does NOT redirect
    # nor does it return a 404. It just goes on as usual. The easiest way is doing this
    # and hoping it doesn't break one day.
    if not r.ok:
        raise req.ConnectionError(f"Got {r.status_code} instead of 200")
    if "not found" not in r.text and "Favorite Games" in r.text:
        return True
    return False
