# pylint: disable=invalid-name
import requests as req

from .constants import SCRUBBY_URL
from ..constants import USER_AGENT


def get_round_source_url(round_id: int) -> str:
    """Gets the source url from a round ID"""
    return req.get(f"{SCRUBBY_URL}{str(round_id)}?raw=true", timeout=10, headers={"User-Agent": USER_AGENT}).json()['baseURL']
