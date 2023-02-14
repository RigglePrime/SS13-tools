import requests as req

from .ban_types import BanData
from .constants import CENTCOM_API_URL
from ..constants import USER_AGENT
from ..byond import canonicalize


def get_one(key: str):
    """Gets bans for a single key"""
    ckey = canonicalize(key)
    resp = req.get(CENTCOM_API_URL.format(ckey=ckey), timeout=10, headers={"User-Agent": USER_AGENT})
    return BanData.from_response(resp)
