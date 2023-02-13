# pylint: disable=invalid-name
# Enable type hinting for static methods
from __future__ import annotations
import json
from typing import Optional, Annotated, Any
from dataclasses import dataclass

from aiohttp import ClientResponse


@dataclass
class RoundData:  # pylint: disable=too-many-instance-attributes
    """Represents round data from Scrubby"""
    roundID: int
    job: Optional[str]
    timestamp: Annotated[str, "ISO 8601, YYYY-MM-DDThh:mm:ss.ffffZ"]
    connectedTime: Annotated[str, "hh:mm:ss.fffffff"]
    roundStartPlayer: bool
    playedInRound: bool
    antagonist: bool
    roundStartSuicide: bool
    isSecurity: bool
    firstSuicide: bool
    firstSuicideEvidence: Optional[Any]
    name: Optional[str]
    server: str

    @staticmethod
    async def from_scrubby_response_async(r: ClientResponse) -> list[RoundData]:
        """Converts a Scrubby JSON response directly to a Python RoundData object"""
        return json.loads(await r.text(), object_hook=lambda d: RoundData(**d))

    # TODO: someone needs to fix this, it's a horrible way to do it
    @staticmethod
    async def should_not_be_used_this_way(round_id: int, timestamp: str, server: str) -> list[RoundData]:
        # This needs to be reworked. heavily. log_downloader is still a mess. Better than before, still a mess.
        # self.rounds is still used, that needs to be reworked since it relies on RoundData (this thing)
        # Right now I'm not in the mood, so I'll push it down for future me.
        """Those lazy devs always up to no good"""
        return RoundData(
            round_id,
            None,
            timestamp,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            server
        )
