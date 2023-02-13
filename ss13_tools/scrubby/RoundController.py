# pylint: disable=invalid-name
from typing import Generator, Iterable
import asyncio
import sys

import requests as req
from aiohttp import ClientSession

from .constants import SCRUBBY_URL
from . import RoundData
from ..constants import USER_AGENT


def get_round_source_url(round_id: int) -> str:
    """Gets the source url from a round ID"""
    return req.get(f"{SCRUBBY_URL}{str(round_id)}?raw=true", timeout=10, headers={"User-Agent": USER_AGENT}).json()['baseURL']


async def get_multiple_round_json(round_ids: Iterable[str]) -> Generator[dict, None, None]:
    """Queries scrubby and retrieves round info JSONs"""
    tasks = []
    async with ClientSession(headers={"User-Agent": USER_AGENT}) as session:
        async def fetch_one(round_id: str):
            async with session.get(f"{SCRUBBY_URL}{str(round_id)}?raw=true") as r:
                if not r.ok:
                    print(f"Request {round_id} returned status {r.status} instead of ok", file=sys.stderr)
                return await r.json()
        for round_id in round_ids:
            round_id = round_id if round_id is str else str(round_id)
            tasks.append(asyncio.ensure_future(fetch_one(round_id)))

        for task in tasks:
            resp = await task
            yield resp
        asyncio.gather(tasks)


async def get_multiple_round_source_urls(round_ids: Iterable[str]) -> Generator[bool, None, None]:
    """Gets source URLs for multiple rounds"""
    async for rnd in get_multiple_round_json(round_ids=round_ids):
        yield rnd['baseURL']


async def round_ids_to_round_data(round_ids: Iterable[str]) -> Generator[RoundData, None, None]:
    """Contructs round data objects from round IDs"""
    async for rnd in get_multiple_round_json(round_ids=round_ids):
        round_info = rnd['currentRound']
        yield RoundData.should_not_be_used_this_way(
            round_id=round_info['id'],
            timestamp=round_info['startTime'],
            server=round_info['server']
        )
