from string import ascii_lowercase, digits
from urllib.parse import quote

import requests as req

from .constants import BYOND_MEMBERS_URL
from ..constants import USER_AGENT


def canonicalize(key: str) -> str:
    """Turns a user's key into canonical form (ckey)"""
    return ''.join([c for c in key.lower() if c in ascii_lowercase + digits + '@'])


def user_exists(key: str) -> bool:
    """Queries the BYOND website and figures out if a user is real"""
    ckey = canonicalize(key)
    # canonicalize should make it url safe but just in case let's also use quote
    resp = req.get(BYOND_MEMBERS_URL.format(ckey=quote(ckey)), timeout=10, headers={"User-Agent": USER_AGENT})
    # The issue here is that when a user doesn't exist, the website does NOT redirect
    # nor does it return a 404. It just goes on as usual. The easiest way is doing this
    # and hoping it doesn't break one day.
    if not resp.ok:
        raise req.ConnectionError(f"Got {resp.status_code} instead of 200")
    if "not found" not in resp.text and "Favorite Games" in resp.text:
        return True
    return False
