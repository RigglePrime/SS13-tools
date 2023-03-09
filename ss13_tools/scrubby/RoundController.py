# pylint: disable=invalid-name
from typing import Generator, Iterable
import asyncio
import sys

import requests as req
from aiohttp import ClientSession

from .constants import ROUND_SOURCE_URL
from . import RoundInfo
from ..constants import USER_AGENT


def get_round_json(round_id: int) -> str:
    """Gets the json info from a round ID"""
    return req.get(ROUND_SOURCE_URL.format(round_id=str(round_id)), timeout=10,
                   headers={"User-Agent": USER_AGENT}).json()


def get_round_source_url(round_id: int) -> str:
    """Gets the source url from a round ID"""
    return get_round_json(round_id=round_id)['currentRound']['baseURL']


async def get_multiple_round_json(round_ids: Iterable[str]) -> Generator[dict, None, None]:
    """Queries scrubby and retrieves round info JSONs"""
    tasks = []
    async with ClientSession(headers={"User-Agent": USER_AGENT}) as session:
        async def fetch_one(round_id: str):
            async with session.get(ROUND_SOURCE_URL.format(round_id=str(round_id))) as resp:
                if not resp.ok:
                    print(f"Request {round_id} returned status {resp.status} instead of ok", file=sys.stderr)
                    return None
                return await resp.json()
        for round_id in round_ids:
            round_id = round_id if round_id is str else str(round_id)
            tasks.append(asyncio.ensure_future(fetch_one(round_id)))

        for task in tasks:
            resp = await task
            yield resp
        await asyncio.gather(*tasks)


async def get_multiple_round_source_urls(round_ids: Iterable[str]) -> Generator[bool, None, None]:
    """Gets source URLs for multiple rounds"""
    async for rnd in get_multiple_round_json(round_ids=round_ids):
        if not rnd:
            continue
        yield rnd['baseURL']


async def get_round_info_from_ids(round_ids: Iterable[str]) -> Generator[RoundInfo, None, None]:
    """Contructs round data resource from round IDs"""
    async for rnd in get_multiple_round_json(round_ids=round_ids):
        if not rnd:
            continue
        round_info = rnd['currentRound']
        yield RoundInfo(
            round_id=round_info['id'],
            timestamp=round_info['startTime'],
            server=round_info['server'].lower().replace('bagil', 'basil').replace(' ', '-')
        )
