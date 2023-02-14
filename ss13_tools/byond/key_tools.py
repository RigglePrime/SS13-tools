from string import ascii_lowercase, digits
from urllib.parse import quote
from typing import Generator
import asyncio
import sys

import requests as req
from aiohttp import ClientSession

from .constants import BYOND_MEMBERS_URL
from ..constants import USER_AGENT


def canonicalize(key: str) -> str:
    """Turns a user's key into canonical form (ckey)"""
    return ''.join([letter for letter in key.lower() if letter in ascii_lowercase + digits + '@'])


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
    if "not found" not in resp.text and '<span>Joined: <span class="info_text">' in resp.text:
        return True
    return False


async def user_exists_many(keys: list[str]) -> Generator[bool, None, None]:
    """Queries the BYOND website and figures out if the users are real"""
    tasks = []
    async with ClientSession(headers={"User-Agent": USER_AGENT}) as session:
        async def fetch_one(ckey: str):
            async with session.get(BYOND_MEMBERS_URL.format(ckey=ckey)) as rsp:
                if not rsp.ok:
                    print(f"Request to {BYOND_MEMBERS_URL} returned status {rsp.status} instead of ok", file=sys.stderr)
                return await rsp.read()
        for key in keys:
            ckey = canonicalize(key)
            # canonicalize should make it url safe but just in case let's also use quote
            tasks.append(asyncio.ensure_future(fetch_one(quote(ckey))))

        # The issue here is that when a user doesn't exist, the website does NOT redirect
        # nor does it return a 404. It just goes on as usual. The easiest way is doing this
        # and hoping it doesn't break one day.
        for task in tasks:
            resp = await task
            yield (b"not found" not in resp and b'<span>Joined: <span class="info_text">' in resp)
        asyncio.gather(tasks)
