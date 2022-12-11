from .ban_types import BanData
from .constants import CENTCOM_API_URL
from byond_tools import canonicalize

import requests as req


def get_one(key: str):
    ckey = canonicalize(key)
    r = req.get(CENTCOM_API_URL.format(ckey=ckey))
    return BanData.from_response(r)
